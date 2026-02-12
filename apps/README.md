# Building demo service images

This repository includes minimal Python services under `apps/otel-shop-lite/src`.

Example image build commands:

```powershell
docker build -f apps/otel-shop-lite/src/frontend/Dockerfile -t ghcr.io/your-org/otel-shop-lite-frontend:v1 apps/otel-shop-lite/src
docker build -f apps/otel-shop-lite/src/catalog-api/Dockerfile -t ghcr.io/your-org/otel-shop-lite-catalog-api:v1 apps/otel-shop-lite/src
docker build -f apps/otel-shop-lite/src/checkout-api/Dockerfile -t ghcr.io/your-org/otel-shop-lite-checkout-api:v1 apps/otel-shop-lite/src
docker build -f apps/otel-shop-lite/src/payment-mock/Dockerfile -t ghcr.io/your-org/otel-shop-lite-payment-mock:v1 apps/otel-shop-lite/src
```

Repeat with `:v2` tags for candidate images.