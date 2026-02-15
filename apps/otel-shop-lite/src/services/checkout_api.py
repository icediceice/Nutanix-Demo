import os

import requests
from flask import jsonify, request


def register(app):
    payment_url = os.getenv("PAYMENT_URL", "http://payment-mock.demo-app.svc.cluster.local")

    @app.route("/checkout", methods=["POST"])
    def checkout():
        body = request.get_json(silent=True) or {}
        payload = {"order_id": body.get("order_id", "demo-order")}
        resp = requests.post(f"{payment_url}/charge", json=payload, timeout=5)
        return jsonify({"checkout": "ok" if resp.ok else "degraded", "payment": resp.json()}), resp.status_code
