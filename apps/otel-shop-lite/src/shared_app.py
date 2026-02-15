import logging
import os
import time

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

from services import SERVICE_REGISTRARS

REQUESTS_TOTAL = Counter("http_requests_total", "HTTP requests", ["service", "method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["service", "method", "path"])
REQUESTS_INSTRUMENTED = False


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


def _instrument_requests_once() -> None:
    global REQUESTS_INSTRUMENTED
    if REQUESTS_INSTRUMENTED:
        return
    RequestsInstrumentor().instrument()
    REQUESTS_INSTRUMENTED = True


def create_app(service_name: str) -> Flask:
    _setup_otel(service_name)
    logger = _setup_logging(service_name)

    app = Flask(service_name)
    FlaskInstrumentor().instrument_app(app)
    _instrument_requests_once()

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

    registrar = SERVICE_REGISTRARS.get(service_name)
    if registrar is None:
        raise ValueError(f"Unknown service name: {service_name}")
    registrar(app)

    return app


def run(service_name: str):
    app = create_app(service_name)
    app.run(host="0.0.0.0", port=8080)
