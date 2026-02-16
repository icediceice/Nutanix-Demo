#!/usr/bin/env python3
import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.request
import urllib.parse


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

        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(req, context=ctx, timeout=timeout) as r:
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
    kommander_sso_user = os.environ.get("KOMMANDER_SSO_USERNAME", "")
    kommander_sso_pass = os.environ.get("KOMMANDER_SSO_PASSWORD", "")
    argocd_user = os.environ.get("ARGOCD_USERNAME", "admin")
    argocd_pass = os.environ.get("ARGOCD_PASSWORD", "")

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

    # Try to discover the management-cluster platform hostname from the SSO redirect.
    # This lets us publish a valid, browser-friendly Kommander UI URL (sslip) instead of an IP/404 root.
    if not kommander_platform_base and (kommander_ingress_probe or kommander_ingress_base):
        probe = kommander_ingress_probe or f"{kommander_ingress_base}/dkp/kubernetes"
        loc = _http_location(probe, insecure_tls=True)
        kommander_platform_base = _url_base(loc)

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
            "kubectl -n argocd port-forward svc/argocd-server 8443:443",
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

    # Grafana
    grafana_ing = f"{kommander_ingress_base}/dkp/logging/grafana" if kommander_ingress_base else _ingress_endpoint("kommander-default-workspace", "grafana-logging")
    if grafana_ing:
        links.append(_build_link(
            "Grafana",
            grafana_ing,
            "ready",
            "Dashboards and metrics (via Kommander ingress + SSO)",
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


def build_payload():
    # ArgoCD app status
    app = k8s_get_json("/apis/argoproj.io/v1alpha1/namespaces/argocd/applications/rx-demo")
    target_rev = get_nested(app, ["spec", "source", "targetRevision"], "unknown")
    sync_status = get_nested(app, ["status", "sync", "status"], "Unknown")
    health_status = get_nested(app, ["status", "health", "status"], "Unknown")
    revision = get_nested(app, ["status", "sync", "revision"], "unknown")

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

    return {
        "now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cd": {
            "engine": "argocd",
            "app": "rx-demo",
            "branch": target_rev,
            "revision": revision,
            "sync": sync_status,
            "health": health_status,
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
        },
        "kpi": [
            {"name": "CD Success Rate", "value": f"{cd_rate}%", "status": "good" if cd_ok else "warn", "threshold": "Synced+Healthy"},
            {"name": "Canary Weight v2", "value": f"{w2}%", "status": "good", "threshold": "informational"},
            {"name": "Policy Compliance", "value": f"{compliance}%", "status": policy_status, "threshold": ">= 95%"},
        ],
        "links": links,
    }


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

            self.send_response(404)
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
