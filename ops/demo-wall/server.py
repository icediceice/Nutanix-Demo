#!/usr/bin/env python3
import argparse
import json
import os
import ssl
import time
import urllib.error
import urllib.request


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
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
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
    }


def serve(port: int):
    from http.server import BaseHTTPRequestHandler, HTTPServer

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

    httpd = HTTPServer(("0.0.0.0", port), Handler)
    httpd.serve_forever()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    serve(args.port)


if __name__ == "__main__":
    main()
