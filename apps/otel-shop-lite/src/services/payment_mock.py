import os
import random
import time

from flask import jsonify, request


def register(app):
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
