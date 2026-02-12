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
            return jsonify({"service": "frontend", "version": os.getenv("SERVICE_VERSION", "unknown"), "status": "ok"})

        @app.route("/checkout", methods=["POST"])
        def frontend_checkout():
            items = requests.get(f"{catalog_url}/items", timeout=5).json()
            payload = request.get_json(silent=True) or {}
            payload["items"] = items
            resp = requests.post(f"{checkout_url}/checkout", json=payload, timeout=5)
            return jsonify({"items": items, "result": resp.json()}), resp.status_code

    return app


def run(service_name: str):
    app = create_app(service_name)
    app.run(host="0.0.0.0", port=8080)