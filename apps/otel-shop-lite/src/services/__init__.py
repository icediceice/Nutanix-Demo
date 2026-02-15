from services.catalog_api import register as register_catalog_api
from services.checkout_api import register as register_checkout_api
from services.frontend import register as register_frontend
from services.payment_mock import register as register_payment_mock

SERVICE_REGISTRARS = {
    "catalog-api": register_catalog_api,
    "checkout-api": register_checkout_api,
    "frontend": register_frontend,
    "payment-mock": register_payment_mock,
}
