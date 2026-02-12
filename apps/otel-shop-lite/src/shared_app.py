import logging
import os
import random
import time

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pythonjsonlogger import jsonlogger

REQUESTS_TOTAL = Counter("http_requests_total", "HTTP requests", ["service", "method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["service", "method", "path"])


def _setup_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _setup_otel(service_name: str) -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger-collector.kommander.svc.cluster.local:4317")
    namespace = os.getenv("OTEL_SERVICE_NAMESPACE", "demo-app")

    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name,
        "service.namespace": namespace,
        "service.version": os.getenv("SERVICE_VERSION", "unknown"),
    }))
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def create_app(service_name: str) -> Flask:
    _setup_otel(service_name)
    logger = _setup_logging(service_name)

    app = Flask(service_name)
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

    @app.before_request
    def _start_timer():
        request._started_at = time.time()

    @app.after_request
    def _record_metrics(resp):
        duration = max(time.time() - getattr(request, "_started_at", time.time()), 0.0)
        REQUESTS_TOTAL.labels(service=service_name, method=request.method, path=request.path, status=str(resp.status_code)).inc()
        REQUEST_LATENCY.labels(service=service_name, method=request.method, path=request.path).observe(duration)

        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None
        trace_id = f"{span_ctx.trace_id:032x}" if span_ctx and span_ctx.is_valid else ""
        span_id = f"{span_ctx.span_id:016x}" if span_ctx and span_ctx.is_valid else ""
        logger.info({
            "service": service_name,
            "level": "info",
            "msg": "request completed",
            "trace_id": trace_id,
            "span_id": span_id,
            "http_method": request.method,
            "http_path": request.path,
            "status_code": resp.status_code,
            "duration_ms": round(duration * 1000.0, 2),
        })
        resp.headers["X-Trace-Id"] = trace_id
        resp.headers["X-Span-Id"] = span_id
        return resp

    @app.route("/metrics", methods=["GET"])
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return jsonify({"status": "ok", "service": service_name})

    if service_name == "catalog-api":
        @app.route("/items", methods=["GET"])
        def items():
            return jsonify([
                {"id": "sku-1", "name": "Nutanix Hoodie", "price": 49.0},
                {"id": "sku-2", "name": "Nutanix Mug", "price": 12.0},
                {"id": "sku-3", "name": "Nutanix Sticker Pack", "price": 6.0},
            ])

    if service_name == "payment-mock":
        @app.route("/charge", methods=["POST"])
        def charge():
            fail_mode = os.getenv("FAIL_MODE", "ok")
            latency_ms = int(os.getenv("LATENCY_MS", "0"))
            error_rate = float(os.getenv("ERROR_RATE", "0"))

            if fail_mode == "latency" and latency_ms > 0:
                time.sleep(latency_ms / 1000.0)

            if fail_mode == "error" and random.random() < error_rate:
                return jsonify({"status": "failed", "reason": "simulated_error", "mode": fail_mode}), 503

            body = request.get_json(silent=True) or {}
            return jsonify({"status": "paid", "order_id": body.get("order_id", "demo"), "mode": fail_mode})

    if service_name == "checkout-api":
        payment_url = os.getenv("PAYMENT_URL", "http://payment-mock.demo-app.svc.cluster.local")

        @app.route("/checkout", methods=["POST"])
        def checkout():
            body = request.get_json(silent=True) or {}
            payload = {"order_id": body.get("order_id", "demo-order")}
            resp = requests.post(f"{payment_url}/charge", json=payload, timeout=5)
            return jsonify({"checkout": "ok" if resp.ok else "degraded", "payment": resp.json()}), resp.status_code

    if service_name == "frontend":
        catalog_url = os.getenv("CATALOG_URL", "http://catalog-api.demo-app.svc.cluster.local")
        checkout_url = os.getenv("CHECKOUT_URL", "http://checkout-api.demo-app.svc.cluster.local")

        @app.route("/", methods=["GET"])
        def index():
            version = os.getenv("SERVICE_VERSION", "unknown")
            is_v2 = version.startswith("v2")
            title = "Nutanix Storefront v2 (Canary Candidate)" if is_v2 else "Nutanix Storefront v1 (Stable)"
            subtitle = (
                "Next-gen experience. This look should increase as canary traffic shifts to v2."
                if is_v2
                else "Stable experience. This look should dominate when traffic stays on v1."
            )
            body_class = "v2" if is_v2 else "v1"
            html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    :root {{
      --v1-bg-1: #e8f3ff;
      --v1-bg-2: #f8fbff;
      --v1-ink: #102136;
      --v1-card: #ffffff;
      --v1-line: #d6e4f5;
      --v1-accent: #0071ce;
      --v1-good: #00a86b;

      --v2-bg-1: #0d1117;
      --v2-bg-2: #111a2a;
      --v2-ink: #f5f8ff;
      --v2-card: #1a2638;
      --v2-line: #32435d;
      --v2-accent: #ff7a18;
      --v2-good: #2dc9a0;

      --danger: #d94b53;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      min-height: 100vh;
    }}
    body.v1 {{
      color: var(--v1-ink);
      background: linear-gradient(160deg, var(--v1-bg-1), var(--v1-bg-2));
    }}
    body.v2 {{
      color: var(--v2-ink);
      background: radial-gradient(circle at top left, #1b2940, var(--v2-bg-1) 55%);
    }}
    .wrap {{ max-width: 960px; margin: 32px auto; padding: 0 16px; }}
    .hero {{
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    body.v1 .hero {{ background: var(--v1-card); border: 1px solid var(--v1-line); }}
    body.v2 .hero {{ background: var(--v2-card); border: 1px solid var(--v2-line); box-shadow: 0 10px 30px rgba(0,0,0,.25); }}
    .title {{ margin: 0 0 8px; font-size: 1.5rem; }}
    .muted {{ margin: 0; }}
    body.v1 .muted {{ color: #4f647b; }}
    body.v2 .muted {{ color: #b8cae8; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }}
    .card {{
      border-radius: 12px;
      padding: 12px;
    }}
    body.v1 .card {{ background: var(--v1-card); border: 1px solid var(--v1-line); }}
    body.v2 .card {{ background: #142033; border: 1px solid #2a3d5d; }}
    .name {{ margin: 0; font-size: 1rem; }}
    .price {{ margin: 8px 0 0; font-weight: 700; }}
    .actions {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      margin: 14px 0 0;
    }}
    button {{
      border: none;
      border-radius: 10px;
      padding: 10px 14px;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
    }}
    body.v1 button {{ background: var(--v1-accent); }}
    body.v2 button {{ background: var(--v2-accent); }}
    button.secondary {{ background: #516d8c !important; }}
    .pill {{
      border-radius: 999px;
      padding: 6px 10px;
      font-size: .85rem;
    }}
    body.v1 .pill {{ border: 1px solid var(--v1-line); background: #fff; }}
    body.v2 .pill {{ border: 1px solid #3d5578; background: #101a2b; color: #d8e6ff; }}
    .status {{
      margin-top: 12px;
      padding: 10px;
      border-radius: 10px;
      font-size: .95rem;
      white-space: pre-wrap;
    }}
    body.v1 .status {{ background: #fff; border: 1px solid var(--v1-line); }}
    body.v2 .status {{ background: #0f1727; border: 1px solid #324768; }}
    body.v1 .ok {{ color: var(--v1-good); }}
    body.v2 .ok {{ color: var(--v2-good); }}
    .bad {{ color: var(--danger); }}
    code {{ padding: 2px 5px; border-radius: 5px; }}
    body.v1 code {{ background: #eef5ff; }}
    body.v2 code {{ background: #1f2e47; color: #dce9ff; }}
  </style>
</head>
<body class="{body_class}">
  <div class="wrap">
    <section class="hero">
      <h1 class="title">{title}</h1>
      <p class="muted">{subtitle}</p>
      <div class="actions">
        <span class="pill">Frontend version: <strong>{version}</strong></span>
        <span class="pill">Canary hint: watch this style shift during rollout</span>
        <span class="pill">Path: <code>/checkout</code></span>
      </div>
    </section>

    <div id="items" class="grid"></div>

    <section class="hero">
      <div class="actions">
        <button id="buy">Run Demo Checkout</button>
        <button id="refresh" class="secondary">Reload Catalog</button>
      </div>
      <div id="status" class="status">Ready.</div>
    </section>
  </div>

  <script>
    const itemsEl = document.getElementById("items");
    const statusEl = document.getElementById("status");

    function setStatus(text, ok=true) {{
      statusEl.textContent = text;
      statusEl.className = "status " + (ok ? "ok" : "bad");
    }}

    async function loadCatalog() {{
      try {{
        const resp = await fetch("/catalog", {{ method: "GET" }});
        const items = await resp.json();
        itemsEl.innerHTML = "";
        items.forEach((it) => {{
          const card = document.createElement("article");
          card.className = "card";
          card.innerHTML = `<h3 class="name">${{it.name}}</h3><p class="muted">SKU: ${{it.id}}</p><p class="price">$${{it.price}}</p>`;
          itemsEl.appendChild(card);
        }});
        setStatus("Catalog loaded. Click 'Run Demo Checkout' to generate live traffic.");
      }} catch (err) {{
        setStatus("Catalog load failed: " + err, false);
      }}
    }}

    async function checkout() {{
      const orderId = "order-" + Date.now();
      try {{
        const resp = await fetch("/checkout", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ order_id: orderId, user: "demo-user" }})
        }});
        const body = await resp.json();
        const traceId = resp.headers.get("X-Trace-Id") || "n/a";
        const frontendVersion = resp.headers.get("X-Frontend-Version") || "{version}";
        const ok = resp.ok;
        setStatus(
          `order_id=${{orderId}}\\nfrontend_version=${{frontendVersion}}\\nstatus=${{resp.status}}\\ntrace_id=${{traceId}}\\nresult=${{JSON.stringify(body)}}`,
          ok
        );
      }} catch (err) {{
        setStatus("Checkout failed: " + err, false);
      }}
    }}

    document.getElementById("buy").addEventListener("click", checkout);
    document.getElementById("refresh").addEventListener("click", loadCatalog);
    loadCatalog();
  </script>
</body>
</html>
"""
            return html, 200, {
                "Content-Type": "text/html; charset=utf-8",
                "X-Frontend-Version": version,
            }

        @app.route("/catalog", methods=["GET"])
        def frontend_catalog():
            resp = requests.get(f"{catalog_url}/items", timeout=5)
            return jsonify(resp.json()), resp.status_code

        @app.route("/api/info", methods=["GET"])
        def frontend_info():
            return jsonify({"service": "frontend", "version": os.getenv("SERVICE_VERSION", "unknown"), "status": "ok"})

        @app.route("/checkout", methods=["POST"])
        def frontend_checkout():
            items = requests.get(f"{catalog_url}/items", timeout=5).json()
            payload = request.get_json(silent=True) or {}
            payload["items"] = items
            resp = requests.post(f"{checkout_url}/checkout", json=payload, timeout=5)
            frontend_version = os.getenv("SERVICE_VERSION", "unknown")
            return (
                jsonify({"items": items, "result": resp.json(), "frontend_version": frontend_version}),
                resp.status_code,
                {"X-Frontend-Version": frontend_version},
            )

    return app


def run(service_name: str):
    app = create_app(service_name)
    app.run(host="0.0.0.0", port=8080)
