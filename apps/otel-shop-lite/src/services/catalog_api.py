from flask import jsonify


def register(app):
    @app.route("/items", methods=["GET"])
    def items():
        return jsonify([
            {"id": "sku-1", "name": "Nutanix Hoodie", "price": 49.0},
            {"id": "sku-2", "name": "Nutanix Mug", "price": 12.0},
            {"id": "sku-3", "name": "Nutanix Sticker Pack", "price": 6.0},
        ])
