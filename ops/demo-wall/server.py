#!/usr/bin/env python3
import argparse
import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
import urllib.parse


SCENARIO_META = {
    "scenario/baseline": {
        "intent": "Stable baseline — 100% traffic to v1, load active",
        "next": "canary-10",
        "watch": [
            {"text": "ArgoCD: Synced + Healthy (both green)",       "tool": "ArgoCD"},
            {"text": "Traffic: 100% v1 · loadgen baseline active"},
            {"text": "Policy: dryrun · 0 violations expected"},
        ],
    },
    "scenario/load-off": {
        "intent": "Load off — cluster at rest, safe to inspect",
        "next": "baseline",
        "watch": [
            {"text": "All pods running · no active traffic"},
            {"text": "Safe moment to walk through any UI or config", "tool": "ArgoCD"},
            {"text": "Switch to baseline to resume the demo"},
        ],
    },
    "scenario/load-peak": {
        "intent": "Peak load — stress-testing v1 capacity",
        "next": "baseline",
        "watch": [
            {"text": "Grafana: elevated RPS on frontend-v1",        "tool": "Grafana"},
            {"text": "Watch CPU / memory creep on pod metrics",     "tool": "Grafana"},
            {"text": "HPA triggers if resource thresholds are hit"},
        ],
    },
    "scenario/canary-10": {
        "intent": "Progressive delivery — 10% traffic shifted to v2",
        "next": "canary-50",
        "watch": [
            {"text": "Kiali: thin green edge to v2 (≈10% of requests)", "tool": "Kiali"},
            {"text": "Jaeger: new traces tagged service.version=v2",     "tool": "Jaeger"},
            {"text": "No error spike → safe to widen the canary"},
        ],
    },
    "scenario/canary-50": {
        "intent": "Progressive delivery — 50 / 50 split, compare RED metrics",
        "next": "canary-100",
        "watch": [
            {"text": "Kiali: equal-weight edges to v1 and v2",          "tool": "Kiali"},
            {"text": "Grafana: compare v1 vs v2 latency side by side",  "tool": "Grafana"},
            {"text": "No regressions → promote to 100%"},
        ],
    },
    "scenario/canary-100": {
        "intent": "Full cutover — 100% traffic on v2",
        "next": "incident-latency",
        "watch": [
            {"text": "Kiali: single thick edge — all traffic on v2",    "tool": "Kiali"},
            {"text": "v1 pods still running · rollback = one patch command"},
            {"text": "Rollback SLA: restore canary-10 in under 3 minutes"},
        ],
    },
    "scenario/incident-latency": {
        "intent": "Incident drill — v2 injecting 1 s latency, watch Jaeger traces",
        "next": "incident-error",
        "watch": [
            {"text": "Jaeger: payment spans show 1 s+ duration on v2", "tool": "Jaeger"},
            {"text": "Grafana: p99 latency spike on payment-mock-v2",   "tool": "Grafana"},
            {"text": "Rollback: patch targetRevision → canary-10 to isolate"},
        ],
    },
    "scenario/incident-error": {
        "intent": "Incident drill — v2 returning 10% errors, watch Kiali graph",
        "next": "baseline",
        "watch": [
            {"text": "Kiali: red error edges on payment-mock-v2 (≈10% 5xx)", "tool": "Kiali"},
            {"text": "Grafana: error rate panel shows spike on v2",           "tool": "Grafana"},
            {"text": "Jaeger: filter by status=ERROR to trace root cause",    "tool": "Jaeger"},
        ],
    },
    "scenario/mirror-v2": {
        "intent": "Traffic mirroring — v2 receives shadow copies silently",
        "next": "baseline",
        "watch": [
            {"text": "Kiali: dashed mirror edge to v2 — zero user impact",  "tool": "Kiali"},
            {"text": "Jaeger: v2 traces appear without affecting v1 users",  "tool": "Jaeger"},
            {"text": "Compare v2 behaviour safely before promoting"},
        ],
    },
    "scenario/keda-checkout": {
        "intent": "Autoscaling — checkout-api scales to zero when idle",
        "next": "baseline",
        "watch": [
            {"text": "KEDA card: checkout-api replicas drop to 0 at rest"},
            {"text": "Send load · watch replicas climb back in real time"},
            {"text": "Grafana: pod count metric reflects scale events",      "tool": "Grafana"},
        ],
    },
    "scenario/quota-pressure": {
        "intent": "Quota pressure — namespace at ~75% pod capacity, guardrails active",
        "next": "baseline",
        "watch": [
            {"text": "Quota card: pod usage approaching namespace limit"},
            {"text": "Gatekeeper: new pods blocked once hard limit is hit"},
            {"text": "Grafana: resource saturation panel turns amber",       "tool": "Grafana"},
        ],
    },
    "scenario/policy-enforce": {
        "intent": "Policy enforcement — Gatekeeper denying non-compliant pods at admission",
        "next": "baseline",
        "watch": [
            {"text": "Policy card: enforcement mode = deny (red badge)"},
            {"text": "Try kubectl apply of a bad pod → admission denied"},
            {"text": "ArgoCD: watch sync status after policy change",        "tool": "ArgoCD"},
        ],
    },
}


def _k8s_request(path: str):
    host = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    url = f"https://{host}:{port}{path}"

    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ca_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

    with open(token_path, "r", encoding="utf-8") as f:
        token = f.read().strip()

    ctx = ssl.create_default_context(cafile=ca_path)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    return urllib.request.urlopen(req, context=ctx, timeout=3)


def k8s_get_json(path: str):
    try:
        with _k8s_request(path) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Return a structured error for visibility in the UI.
        return {"_error": f"HTTP {e.code} for {path}"}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


def _k8s_patch_json(path: str, body: dict):
    """PATCH a k8s resource with merge-patch+json. Returns parsed JSON or {_error:...}."""
    host = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    url = f"https://{host}:{port}{path}"
    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ca_path    = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            token = f.read().strip()
        ctx  = ssl.create_default_context(cafile=ca_path)
        data = json.dumps(body).encode("utf-8")
        req  = urllib.request.Request(url, data=data, method="PATCH")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type",  "application/merge-patch+json")
        req.add_header("Accept",        "application/json")
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        return {"_error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


def _read_secret_b64(namespace: str, name: str, key: str) -> str:
    """Read a base64-encoded value from a k8s Secret. Returns '' on any error."""
    secret = k8s_get_json(f"/api/v1/namespaces/{namespace}/secrets/{name}")
    if "_error" in secret:
        return ""
    raw = (secret.get("data") or {}).get(key, "")
    if not raw:
        return ""
    try:
        return base64.b64decode(raw).decode("utf-8").strip()
    except Exception:
        return ""


_KOMMANDER_CRED_CANDIDATES = [
    ("kommander",                   "dkp-credentials",             "username", "password"),
    ("kommander-default-workspace", "dkp-credentials",             "username", "password"),
    ("kommander-default-workspace", "dkp-admin-user-password",     "",         "password"),
    ("kommander",                   "dkp-admin-user-password",     "",         "password"),
    ("kommander-default-workspace", "kommander-admin-credentials", "",         "password"),
    ("kommander",                   "kommander-admin-credentials", "",         "password"),
]


def _discover_kommander_password() -> str:
    """Try known NKP/DKP secret locations for the SSO admin password."""
    for ns, sname, _ukey, pkey in _KOMMANDER_CRED_CANDIDATES:
        val = _read_secret_b64(ns, sname, pkey)
        if val:
            return val
    return ""


def _discover_kommander_username() -> str:
    """Try known NKP/DKP secret locations for the SSO admin username."""
    for ns, sname, ukey, pkey in _KOMMANDER_CRED_CANDIDATES:
        if ukey and _read_secret_b64(ns, sname, pkey):
            val = _read_secret_b64(ns, sname, ukey)
            if val:
                return val
    return ""


def get_nested(obj, keys, default=None):
    cur = obj
    for k in keys:
        if isinstance(cur, dict):
            if k not in cur:
                return default
            cur = cur[k]
            continue
        if isinstance(cur, list) and isinstance(k, int):
            if k < 0 or k >= len(cur):
                return default
            cur = cur[k]
            continue
        return default
    return cur


def extract_vs_weights(vs):
    try:
        http = (vs.get("spec") or {}).get("http") or []
        if not http:
            return (0, 0)
        routes = http[0].get("route") or []
        v1 = 0
        v2 = 0
        for r in routes:
            dest = (r.get("destination") or {})
            subset = dest.get("subset")
            w = int(r.get("weight") or 0)
            if subset == "v1":
                v1 = w
            if subset == "v2":
                v2 = w
        return (v1, v2)
    except Exception:
        return (0, 0)


def _first_non_empty(values):
    for v in values:
        if v:
            return v
    return ""


def _service_port(service_obj, preferred_ports=None):
    preferred_ports = preferred_ports or []
    ports = get_nested(service_obj, ["spec", "ports"], []) or []
    if not ports:
        return 0
    for wanted in preferred_ports:
        for p in ports:
            if int(p.get("port") or 0) == int(wanted):
                return int(p.get("port") or 0)
    return int(ports[0].get("port") or 0)


def _service_lb_url(service_obj, preferred_ports=None, default_scheme="http"):
    ingress = get_nested(service_obj, ["status", "loadBalancer", "ingress"], []) or []
    if not ingress:
        return ""
    host = _first_non_empty([ingress[0].get("hostname"), ingress[0].get("ip")])
    if not host:
        return ""
    port = _service_port(service_obj, preferred_ports=preferred_ports)
    scheme = "https" if port == 443 else default_scheme
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        return f"{scheme}://{host}/"
    return f"{scheme}://{host}:{port}/"


def _list_services(namespace):
    data = k8s_get_json(f"/api/v1/namespaces/{namespace}/services")
    if "_error" in data:
        return []
    return data.get("items") or []


def _find_service(namespaces, name_tokens=None, preferred_ports=None):
    name_tokens = [t.lower() for t in (name_tokens or [])]
    preferred_ports = preferred_ports or []
    best = None
    best_score = -1

    for ns in namespaces:
        for svc in _list_services(ns):
            name = get_nested(svc, ["metadata", "name"], "").lower()
            labels = get_nested(svc, ["metadata", "labels"], {}) or {}
            label_blob = " ".join([f"{k}={v}" for k, v in labels.items()]).lower()
            ports = get_nested(svc, ["spec", "ports"], []) or []
            port_values = {int(p.get("port") or 0) for p in ports}

            score = 0
            if any(tok in name for tok in name_tokens):
                score += 4
            if any(tok in label_blob for tok in name_tokens):
                score += 2
            if preferred_ports and any(int(p) in port_values for p in preferred_ports):
                score += 3
            if score <= 0:
                continue
            if score > best_score:
                best_score = score
                best = (ns, svc)

    return best


def _ingress_link(namespace):
    data = k8s_get_json(f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses")
    if "_error" in data:
        return ""
    for ing in data.get("items") or []:
        host = _first_non_empty([
            get_nested(ing, ["status", "loadBalancer", "ingress", 0, "hostname"], ""),
            get_nested(ing, ["status", "loadBalancer", "ingress", 0, "ip"], ""),
            get_nested(ing, ["spec", "rules", 0, "host"], ""),
        ])
        if host:
            return f"https://{host}/"
    return ""


def _ingress_endpoint(namespace, name, default_scheme="https"):
    ing = k8s_get_json(f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}")
    if "_error" in ing:
        return ""

    host = _first_non_empty([
        get_nested(ing, ["status", "loadBalancer", "ingress", 0, "hostname"], ""),
        get_nested(ing, ["status", "loadBalancer", "ingress", 0, "ip"], ""),
        get_nested(ing, ["spec", "rules", 0, "host"], ""),
    ])
    if not host:
        return ""

    path = get_nested(ing, ["spec", "rules", 0, "http", "paths", 0, "path"], "/")
    if not path:
        path = "/"
    if not str(path).startswith("/"):
        path = f"/{path}"
    return f"{default_scheme}://{host}{path}"


def _http_location(url: str, timeout: int = 3, insecure_tls: bool = False) -> str:
    try:
        ctx = ssl._create_unverified_context() if insecure_tls else ssl.create_default_context()
        req = urllib.request.Request(url, method="GET")
        # Don't follow redirects; we want the initial Location header.
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(
            _NoRedirect(),
            urllib.request.HTTPSHandler(context=ctx),
        )
        try:
            with opener.open(req, timeout=timeout) as r:
                # If it didn't redirect, Location won't exist.
                return r.headers.get("Location", "") or ""
        except urllib.error.HTTPError as e:
            # urllib raises for 30x unless redirect handler follows it. We want the 30x Location.
            return e.headers.get("Location", "") or ""
    except Exception:
        return ""


def _url_base(url: str) -> str:
    try:
        p = urllib.parse.urlparse(url)
        if not p.scheme or not p.netloc:
            return ""
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return ""


def _parse_ini_value(text: str, key: str) -> str:
    # Minimal INI-ish parser for "key = value" lines.
    try:
        for raw in (text or "").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() != key:
                continue
            val = v.strip().strip("\"").strip("'")
            return val
    except Exception:
        return ""
    return ""


def _list_ingress_paths(namespace: str):
    data = k8s_get_json(f"/apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses")
    if "_error" in data:
        return []
    paths = []
    for ing in data.get("items") or []:
        for rule in (ing.get("spec") or {}).get("rules") or []:
            http = (rule.get("http") or {})
            for p in http.get("paths") or []:
                path = p.get("path")
                if not path:
                    continue
                if not str(path).startswith("/"):
                    path = f"/{path}"
                paths.append(str(path))
    # De-dupe while preserving order.
    seen = set()
    out = []
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _pick_platform_entry_path(paths):
    # Prefer Kommander/NKP landing pages if present, otherwise any /dkp/* route.
    preferred = [
        "/dkp/kommander",
        "/dkp/kommander/",
        "/dkp/insights",
        "/dkp/insights/",
        "/dkp/kubernetes",
        "/dkp/kubernetes/",
        "/dkp/grafana",
        "/dkp/grafana/",
    ]
    for p in preferred:
        if p in paths:
            return p
    for p in paths:
        if p.startswith("/dkp/"):
            return p
    return ""


def _build_link(name, url, status, hint="", command="", username="", password=""):
    return {
        "name": name,
        "url": url,
        "status": status,
        "hint": hint,
        "command": command,
        "username": username,
        "password": password,
    }


def build_quick_links():
    links = []

    # Credentials: env vars take precedence; fall back to auto-discovery from cluster secrets.
    argocd_user = os.environ.get("ARGOCD_USERNAME", "admin")
    argocd_pass = (
        os.environ.get("ARGOCD_PASSWORD", "")
        or _read_secret_b64("argocd", "argocd-initial-admin-secret", "password")
    )
    kommander_sso_user = (
        os.environ.get("KOMMANDER_SSO_USERNAME", "")
        or _discover_kommander_username()
        or "admin"
    )
    kommander_sso_pass = (
        os.environ.get("KOMMANDER_SSO_PASSWORD", "")
        or _discover_kommander_password()
    )

    kommander_ingress_base = ""
    kommander_ingress_probe = ""
    kommander_platform_base = os.environ.get("KOMMANDER_PLATFORM_BASE", "")
    kommander_traefik = k8s_get_json("/api/v1/namespaces/kommander-default-workspace/services/kommander-traefik")
    if "_error" not in kommander_traefik:
        host = _first_non_empty([
            get_nested(kommander_traefik, ["status", "loadBalancer", "ingress", 0, "hostname"], ""),
            get_nested(kommander_traefik, ["status", "loadBalancer", "ingress", 0, "ip"], ""),
        ])
        if host:
            kommander_ingress_base = f"https://{host}"

        # Prefer probing via ClusterIP to avoid "hairpin" issues reaching the LoadBalancer IP from pods.
        cluster_ip = get_nested(kommander_traefik, ["spec", "clusterIP"], "")
        if cluster_ip and str(cluster_ip).lower() != "none":
            port = _service_port(kommander_traefik, preferred_ports=[443, 80])
            scheme = "https" if int(port or 0) == 443 else "http"
            if port and ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
                kommander_ingress_probe = f"{scheme}://{cluster_ip}/dkp/kubernetes"
            elif port:
                kommander_ingress_probe = f"{scheme}://{cluster_ip}:{port}/dkp/kubernetes"

    # Preferred discovery path: read the traefik-forward-auth provider-uri (Dex base).
    if not kommander_platform_base:
        tfa_cfg = k8s_get_json("/api/v1/namespaces/kommander-default-workspace/configmaps/traefik-forward-auth-configmap")
        if "_error" not in tfa_cfg:
            provider_uri = _parse_ini_value(get_nested(tfa_cfg, ["data", "config"], ""), "provider-uri")
            base = _url_base(provider_uri)
            # Example provider-uri: https://nkp-10-38-56-16.sslip.nutanixdemo.com/dex
            if base:
                kommander_platform_base = base

    # Try to discover the management-cluster platform hostname from the SSO redirect.
    # This lets us publish a valid, browser-friendly Kommander UI URL instead of a raw IP/404 root.
    if not kommander_platform_base and (kommander_ingress_probe or kommander_ingress_base):
        probe = kommander_ingress_probe or f"{kommander_ingress_base}/dkp/kubernetes"
        loc = _http_location(probe, insecure_tls=True)
        base = _url_base(loc)
        # Accept the redirect as long as it isn't pointing back at the workload ingress itself.
        # (Previously filtered for "sslip" only — this is now cluster-agnostic.)
        workload_base = kommander_ingress_base.rstrip("/")
        if base and base.rstrip("/") != workload_base:
            kommander_platform_base = base

    # Demo app
    app_svc = k8s_get_json("/api/v1/namespaces/istio-helm-gateway-ns/services/istio-helm-ingressgateway")
    if "_error" in app_svc:
        links.append(_build_link(
            "Demo App",
            "",
            "pending",
            "Waiting for storefront ingress service",
        ))
    else:
        app_url = _service_lb_url(app_svc, preferred_ports=[80], default_scheme="http")
        if app_url:
            links.append(_build_link(
                "Demo App",
                app_url,
                "ready",
                "Storefront ingress URL",
            ))
        else:
            links.append(_build_link(
                "Demo App",
                "http://localhost:8080/",
                "local",
                "Storefront ingress URL via port-forward",
                "kubectl -n istio-helm-gateway-ns port-forward svc/istio-helm-ingressgateway 8080:80",
            ))

    # ArgoCD
    argo_svc = k8s_get_json("/api/v1/namespaces/argocd/services/argocd-server")
    if "_error" in argo_svc:
        links.append(_build_link(
            "ArgoCD",
            "",
            "pending",
            "Waiting for ArgoCD service",
            username=argocd_user,
            password=argocd_pass,
        ))
    else:
        argo_url = _service_lb_url(argo_svc, preferred_ports=[443], default_scheme="https")
        links.append(_build_link(
            "ArgoCD",
            argo_url or "https://localhost:8443/",
            "ready" if argo_url else "local",
            "GitOps control plane",
            "" if argo_url else "kubectl -n argocd port-forward svc/argocd-server 8443:443",
            argocd_user,
            argocd_pass,
        ))

    # Kiali
    kiali_ing = f"{kommander_ingress_base}/dkp/kiali" if kommander_ingress_base else _ingress_endpoint("kommander-default-workspace", "kiali")
    if kiali_ing:
        links.append(_build_link(
            "Kiali",
            kiali_ing,
            "ready",
            "Service graph and traffic health (via Kommander ingress + SSO)",
            username=kommander_sso_user,
            password=kommander_sso_pass,
        ))
    else:
        kiali = _find_service(
        namespaces=["istio-system", "kommander-default-workspace", "kommander"],
        name_tokens=["kiali"],
        preferred_ports=[20001, 80],
        )
        if kiali:
            ns, svc = kiali
            remote = _service_lb_url(svc, preferred_ports=[20001, 80], default_scheme="http")
            port = _service_port(svc, preferred_ports=[20001, 80])
            links.append(_build_link(
                "Kiali",
                remote or "http://localhost:20001/",
                "ready" if remote else "local",
                "Service graph and traffic health",
                f"kubectl -n {ns} port-forward svc/{get_nested(svc, ['metadata', 'name'], 'kiali')} 20001:{port or 20001}",
                kommander_sso_user,
                kommander_sso_pass,
            ))
        else:
            links.append(_build_link(
                "Kiali",
                "",
                "pending",
                "Waiting for Kiali service",
                username=kommander_sso_user,
                password=kommander_sso_pass,
            ))

    # Jaeger
    jaeger_ing = f"{kommander_ingress_base}/dkp/jaeger" if kommander_ingress_base else _ingress_endpoint("istio-system", "jaeger-jaeger-operator-jaeger-query")
    if jaeger_ing:
        links.append(_build_link(
            "Jaeger",
            jaeger_ing,
            "ready",
            "Distributed traces (via Kommander ingress + SSO)",
            username=kommander_sso_user,
            password=kommander_sso_pass,
        ))
    else:
        jaeger = _find_service(
        namespaces=["istio-system", "kommander-default-workspace", "kommander"],
        name_tokens=["jaeger", "query"],
        preferred_ports=[16686, 80],
        )
        if jaeger:
            ns, svc = jaeger
            remote = _service_lb_url(svc, preferred_ports=[16686, 80], default_scheme="http")
            port = _service_port(svc, preferred_ports=[16686, 80])
            links.append(_build_link(
                "Jaeger",
                remote or "http://localhost:16686/",
                "ready" if remote else "local",
                "Distributed traces",
                f"kubectl -n {ns} port-forward svc/{get_nested(svc, ['metadata', 'name'], 'jaeger-query')} 16686:{port or 16686}",
                kommander_sso_user,
                kommander_sso_pass,
            ))
        else:
            links.append(_build_link(
                "Jaeger",
                "",
                "pending",
                "Waiting for Jaeger query service",
                username=kommander_sso_user,
                password=kommander_sso_pass,
            ))

    # Grafana — use /dkp/grafana (metrics/Prometheus Grafana) not /dkp/logging/grafana (Loki)
    grafana_ing = f"{kommander_ingress_base}/dkp/grafana" if kommander_ingress_base else _ingress_endpoint("kommander-default-workspace", "grafana-logging")
    if grafana_ing:
        links.append(_build_link(
            "Grafana",
            grafana_ing,
            "ready",
            "RED metrics & dashboards (via Kommander ingress + SSO)",
            username=kommander_sso_user,
            password=kommander_sso_pass,
        ))
    else:
        grafana = _find_service(
        namespaces=["kommander-default-workspace", "kommander", "monitoring"],
        name_tokens=["grafana"],
        preferred_ports=[3000, 80],
        )
        if grafana:
            ns, svc = grafana
            remote = _service_lb_url(svc, preferred_ports=[3000, 80], default_scheme="http")
            port = _service_port(svc, preferred_ports=[3000, 80])
            links.append(_build_link(
                "Grafana",
                remote or "http://localhost:3000/",
                "ready" if remote else "local",
                "Dashboards and metrics",
                f"kubectl -n {ns} port-forward svc/{get_nested(svc, ['metadata', 'name'], 'grafana')} 3000:{port or 3000}",
                kommander_sso_user,
                kommander_sso_pass,
            ))
        else:
            links.append(_build_link(
                "Grafana",
                "",
                "pending",
                "Waiting for Grafana service",
                username=kommander_sso_user,
                password=kommander_sso_pass,
            ))

    # Kommander ingress (optional, management cluster workspace)
    kommander_url = _ingress_link("kommander")
    if not kommander_url:
        # Prefer the platform hostname if we can discover it (typically has a valid TLS cert).
        if kommander_platform_base:
            kommander_url = f"{kommander_platform_base}/dkp/kommander/dashboard/"
        elif kommander_ingress_base:
            # Fallback to a known-good /dkp entry point on the workload ingress.
            # Root (/) is often not a UI landing page (can map to object store or 404).
            paths = _list_ingress_paths("kommander-default-workspace")
            entry = _pick_platform_entry_path(paths)
            if entry:
                kommander_url = f"{kommander_ingress_base}{entry}"
            else:
                kommander_url = f"{kommander_ingress_base}/dkp/kubernetes"

    if kommander_url:
        links.append(_build_link(
            "Kommander",
            kommander_url,
            "ready",
            "Platform UI",
            username=kommander_sso_user,
            password=kommander_sso_pass,
        ))
    else:
        links.append(_build_link(
            "Kommander",
            "",
            "pending",
            "Waiting for platform ingress",
            username=kommander_sso_user,
            password=kommander_sso_pass,
        ))

    return links


def get_quota_status():
    """Return ResourceQuota usage for demo-app namespace."""
    data = k8s_get_json("/api/v1/namespaces/demo-app/resourcequotas")
    if "_error" in data:
        return {"available": False}
    items = data.get("items") or []
    if not items:
        return {"available": False}
    quota = items[0]
    hard = (quota.get("status") or {}).get("hard") or {}
    used = (quota.get("status") or {}).get("used") or {}

    def parse_quantity(val, scale=1):
        try:
            v = str(val or "0").strip()
            if v.endswith("m"):
                return float(v[:-1]) / 1000.0
            if v.endswith("Ki"):
                return float(v[:-2]) * 1024 / scale
            if v.endswith("Mi"):
                return float(v[:-2]) * 1024 * 1024 / scale
            if v.endswith("Gi"):
                return float(v[:-2]) * 1024 * 1024 * 1024 / scale
            return float(v)
        except Exception:
            return 0.0

    pods_used  = int(used.get("pods", 0) or 0)
    pods_hard  = int(hard.get("pods", 0) or 0)
    cpu_used   = parse_quantity(used.get("requests.cpu", "0"))
    cpu_hard   = parse_quantity(hard.get("requests.cpu", "0"))
    mem_used   = parse_quantity(used.get("requests.memory", "0"), scale=1024*1024)
    mem_hard   = parse_quantity(hard.get("requests.memory", "0"), scale=1024*1024)

    pods_pct = round((pods_used / pods_hard * 100), 1) if pods_hard > 0 else 0.0
    pods_status = "good" if pods_pct < 70 else ("warn" if pods_pct < 90 else "bad")

    return {
        "available": True,
        "pods": {"used": pods_used, "hard": pods_hard, "pct": pods_pct, "status": pods_status},
        "cpu":  {"used": round(cpu_used, 2), "hard": round(cpu_hard, 2)},
        "mem":  {"used": round(mem_used, 0), "hard": round(mem_hard, 0)},
    }


def get_keda_status():
    """Return KEDA ScaledObject state for checkout-api-v1; {enabled:False} when not present."""
    so = k8s_get_json("/apis/keda.sh/v1alpha1/namespaces/demo-app/scaledobjects/checkout-api-v1-keda")
    if "_error" in so:
        return {"enabled": False}

    conditions = get_nested(so, ["status", "conditions"], []) or []
    active = any(
        c.get("type") == "Active" and c.get("status") == "True"
        for c in conditions
    )

    deploy = k8s_get_json("/apis/apps/v1/namespaces/demo-app/deployments/checkout-api-v1")
    current = 0 if "_error" in deploy else (get_nested(deploy, ["status", "readyReplicas"], 0) or 0)

    return {
        "enabled": True,
        "active": active,
        "currentReplicas": current,
        "minReplicas": get_nested(so, ["spec", "minReplicaCount"], 0),
        "maxReplicas": get_nested(so, ["spec", "maxReplicaCount"], 10),
    }


def _resolve_watch(watch_items, links):
    """Resolve tool names in watch points to discovered URLs."""
    link_map = {l["name"]: l.get("url", "") for l in links if l.get("url")}
    return [
        {"text": w["text"], "url": link_map.get(w.get("tool", ""), "")}
        for w in watch_items
    ]


def build_workloads():
    """Return replica health for all deployments in demo-app namespace."""
    data = k8s_get_json("/apis/apps/v1/namespaces/demo-app/deployments")
    if "_error" in data:
        return []
    result = []
    for item in (data.get("items") or []):
        name    = get_nested(item, ["metadata", "name"], "?")
        desired = get_nested(item, ["spec", "replicas"], 0) or 0
        ready   = get_nested(item, ["status", "readyReplicas"], 0) or 0
        image   = get_nested(item, ["spec", "template", "spec", "containers", 0, "image"], "")
        tag     = image.split(":")[-1] if ":" in image else image
        status  = "good" if (ready >= desired and desired > 0) else ("warn" if ready > 0 else "bad")
        result.append({"name": name, "ready": ready, "desired": desired, "tag": tag, "status": status})
    return sorted(result, key=lambda x: x["name"])


def build_payload():
    # ArgoCD app status
    app = k8s_get_json("/apis/argoproj.io/v1alpha1/namespaces/argocd/applications/rx-demo")
    target_rev = get_nested(app, ["spec", "source", "targetRevision"], "unknown")
    sync_status = get_nested(app, ["status", "sync", "status"], "Unknown")
    health_status = get_nested(app, ["status", "health", "status"], "Unknown")
    revision = get_nested(app, ["status", "sync", "revision"], "unknown")
    meta = SCENARIO_META.get(target_rev, {"intent": "", "next": ""})

    # Loadgen
    load = k8s_get_json("/apis/apps/v1/namespaces/demo-ops/deployments/demo-loadgen")
    desired = get_nested(load, ["spec", "replicas"], -1)
    ready = get_nested(load, ["status", "readyReplicas"], 0)
    profile = "off" if isinstance(desired, int) and desired <= 0 else "active"

    # Canary weights: prefer ingress VS if present, fallback to mesh VS
    vs_ing = k8s_get_json("/apis/networking.istio.io/v1/namespaces/demo-app/virtualservices/frontend-ingress")
    if "_error" in vs_ing:
        vs_ing = k8s_get_json("/apis/networking.istio.io/v1/namespaces/demo-app/virtualservices/frontend")
    w1, w2 = extract_vs_weights(vs_ing)

    # Gatekeeper constraints (cluster-scoped)
    constraints = [
        ("demo-required-labels", "/apis/constraints.gatekeeper.sh/v1beta1/k8sdemorequiredlabels/demo-required-labels"),
        ("demo-required-resources", "/apis/constraints.gatekeeper.sh/v1beta1/k8sdemorequiredresources/demo-required-resources"),
        ("demo-no-latest", "/apis/constraints.gatekeeper.sh/v1beta1/k8sdemonolatest/demo-no-latest"),
    ]
    policy_total = 0
    pass_count = 0
    warn_violations = 0
    for _, path in constraints:
        c = k8s_get_json(path)
        if "_error" in c:
            continue
        policy_total += 1
        v = get_nested(c, ["status", "totalViolations"], 0)
        try:
            v = int(v)
        except Exception:
            v = 0
        if v > 0:
            warn_violations += v
        else:
            pass_count += 1

    compliance = round((pass_count / policy_total) * 100.0, 1) if policy_total > 0 else 100.0
    policy_status = "good" if compliance >= 95 else ("warn" if compliance >= 60 else "bad")

    # Simple CD KPI
    cd_ok = (sync_status == "Synced" and health_status == "Healthy")
    cd_rate = 100.0 if cd_ok else (50.0 if health_status in ("Progressing", "Suspended") else 0.0)
    links = build_quick_links()
    keda = get_keda_status()
    quota = get_quota_status()
    workloads = build_workloads()

    return {
        "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cd": {
            "engine": "argocd",
            "app": "rx-demo",
            "branch": target_rev,
            "revision": revision,
            "sync": sync_status,
            "health": health_status,
            "intent": meta["intent"],
            "next": meta["next"],
            "watch": _resolve_watch(meta.get("watch", []), links),
        },
        "loadgen": {
            "desiredReplicas": desired,
            "readyReplicas": ready,
            "profile": profile,
        },
        "canary": {"v1": w1, "v2": w2},
        "policy": {
            "pass": pass_count,
            "warn": warn_violations,
            "fail": 0,
            "error": 0,
            "compliance": compliance,
            "status": policy_status,
            "enforcing": target_rev == "scenario/policy-enforce",
        },
        "kpi": [
            {"name": "CD Success Rate", "value": f"{cd_rate}%", "status": "good" if cd_ok else "warn", "threshold": "Synced+Healthy"},
            {"name": "Canary Weight v2", "value": f"{w2}%", "status": "good", "threshold": "informational"},
            {"name": "Policy Compliance", "value": f"{compliance}%", "status": policy_status, "threshold": ">= 95%"},
        ],
        "keda": keda,
        "quota": quota,
        "workloads": workloads,
        "links": links,
        "scenarios": [
            {"branch": k, "intent": v["intent"], "next": v.get("next", "")}
            for k, v in SCENARIO_META.items()
        ],
    }


def switch_scenario(branch: str):
    """Patch ArgoCD Application targetRevision and trigger a hard refresh."""
    if branch not in SCENARIO_META:
        return {"ok": False, "error": f"Unknown branch: {branch!r}"}
    result = _k8s_patch_json(
        "/apis/argoproj.io/v1alpha1/namespaces/argocd/applications/rx-demo",
        {"spec": {"source": {"targetRevision": branch}}},
    )
    if "_error" in result:
        return {"ok": False, "error": result["_error"]}
    # Trigger ArgoCD hard refresh — best-effort, ignore errors
    _k8s_patch_json(
        "/apis/argoproj.io/v1alpha1/namespaces/argocd/applications/rx-demo",
        {"metadata": {"annotations": {"argocd.argoproj.io/refresh": "hard"}}},
    )
    return {"ok": True, "branch": branch}


def serve(port: int):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    here = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(here, "index.html")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                with open(index_path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return

            if self.path == "/healthz":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(b"ok")
                return

            if self.path == "/api/status":
                payload = build_payload()
                data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return

            if self.path in ("/quickref", "/quickref.html"):
                qr_path = os.path.join(here, "quickref.html")
                try:
                    with open(qr_path, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(data)
                except FileNotFoundError:
                    self.send_response(404)
                    self.end_headers()
                return

            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            if self.path == "/api/switch-scenario":
                length = int(self.headers.get("Content-Length", 0) or 0)
                raw = self.rfile.read(length) if length > 0 else b"{}"
                try:
                    req_data = json.loads(raw.decode("utf-8"))
                except Exception:
                    req_data = {}
                branch = str(req_data.get("branch", ""))
                result = switch_scenario(branch)
                data = json.dumps(result, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_response(405)
            self.end_headers()

        def log_message(self, fmt, *args):
            # keep logs quiet
            return

    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    httpd.serve_forever()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    serve(args.port)


if __name__ == "__main__":
    main()
