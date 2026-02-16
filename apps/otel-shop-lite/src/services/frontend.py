import os

import requests
from flask import jsonify, request


def _render_frontend(version: str) -> tuple[str, str]:
    is_v2 = version.startswith("v2")
    title = "Nutanix Storefront"
    subtitle = "Browse products, open product pages, and run checkout from one clean control panel."
    body_class = "v2" if is_v2 else "v1"
    stage = "v2 candidate" if is_v2 else "v1 stable"
    banner = "CANARY EXPERIENCE" if is_v2 else "STABLE EXPERIENCE"
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --v1-bg: #edf3fb;
      --v1-card: #ffffff;
      --v1-line: #c8d7ea;
      --v1-ink: #11243d;
      --v1-muted: #4a6485;
      --v1-brand: #0a5cc2;
      --v1-brand-soft: #e5f0ff;
      --v1-good: #0d9f74;

      --v2-bg: #0f1724;
      --v2-card: #172337;
      --v2-line: #324866;
      --v2-ink: #f2f7ff;
      --v2-muted: #b5c8e5;
      --v2-brand: #ff8c42;
      --v2-brand-soft: #2a1f18;
      --v2-good: #38d2ac;

      --bad: #e24a4a;
      --radius: 14px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Work Sans", "Segoe UI", sans-serif;
      min-height: 100vh;
    }
    body.v1 { background: linear-gradient(160deg, #ffffff 0%, var(--v1-bg) 75%); color: var(--v1-ink); }
    body.v2 { background: radial-gradient(circle at 10% 10%, #1e2c43 0%, var(--v2-bg) 60%); color: var(--v2-ink); }
    .wrap { max-width: 1180px; margin: 24px auto; padding: 0 16px; }
    .top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 14px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-family: "Sora", "Work Sans", sans-serif;
      font-weight: 700;
    }
    .brand-mark {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      color: #fff;
      font-size: 0.9rem;
      font-weight: 700;
    }
    body.v1 .brand-mark { background: linear-gradient(145deg, #0a5cc2, #44a5ff); }
    body.v2 .brand-mark { background: linear-gradient(145deg, #ff8c42, #ffc18c); color: #2c1a0f; }
    .tag {
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 600;
      border: 1px solid;
    }
    body.v1 .tag { color: #1f4e87; border-color: #a8c4e8; background: #f2f7ff; }
    body.v2 .tag { color: #ffd4b7; border-color: #5d4c3f; background: #2a1f18; }
    .hero {
      border-radius: var(--radius);
      border: 1px solid;
      padding: 16px;
      margin-bottom: 14px;
    }
    body.v1 .hero { background: var(--v1-card); border-color: var(--v1-line); }
    body.v2 .hero { background: var(--v2-card); border-color: var(--v2-line); }
    .hero h1 {
      margin: 0;
      font-family: "Sora", "Work Sans", sans-serif;
      font-size: clamp(1.35rem, 2.2vw, 1.9rem);
    }
    .hero p { margin: 8px 0 0; color: inherit; opacity: 0.86; }
    .banner {
      margin-top: 12px;
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
      letter-spacing: 0.03em;
      border: 1px solid;
    }
    body.v1 .banner { background: var(--v1-brand-soft); border-color: #b5d0f0; color: #1f4f88; }
    body.v2 .banner { background: var(--v2-brand-soft); border-color: #5d4c3f; color: #ffd4b7; }
    .layout {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 14px;
    }
    .panel {
      border-radius: var(--radius);
      border: 1px solid;
      padding: 14px;
    }
    body.v1 .panel { background: var(--v1-card); border-color: var(--v1-line); }
    body.v2 .panel { background: var(--v2-card); border-color: var(--v2-line); }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }
    button {
      border: none;
      border-radius: 10px;
      padding: 9px 12px;
      cursor: pointer;
      font-family: "Work Sans", sans-serif;
      font-weight: 600;
    }
    body.v1 button { background: var(--v1-brand); color: #fff; }
    body.v2 button { background: var(--v2-brand); color: #2b190f; }
    button.secondary { background: #607792 !important; color: #fff !important; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }
    .card {
      border-radius: 12px;
      border: 1px solid;
      padding: 10px;
    }
    body.v1 .card { border-color: #c8d7ea; background: #fff; }
    body.v2 .card { border-color: #354e70; background: #162235; }
    .thumb {
      border-radius: 10px;
      min-height: 98px;
      padding: 10px;
      display: flex;
      justify-content: space-between;
      align-items: end;
      color: #fff;
      font-weight: 600;
      margin-bottom: 8px;
      cursor: pointer;
    }
    .sku {
      font-size: 0.76rem;
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 999px;
      padding: 3px 7px;
      background: rgba(255,255,255,0.18);
    }
    .name { margin: 0; font-weight: 700; }
    .meta { margin: 5px 0 0; font-size: 0.83rem; opacity: 0.85; min-height: 32px; }
    .row { margin-top: 8px; display: flex; justify-content: space-between; align-items: center; gap: 8px; }
    .price { font-weight: 700; }
    .small {
      font-size: 0.8rem;
      padding: 5px 8px;
      border-radius: 8px;
      border: 1px solid;
      background: transparent;
    }
    body.v1 .small { color: #315986; border-color: #a6c2e5; }
    body.v2 .small { color: #c4d8f8; border-color: #4a668c; }
    .panel h2 {
      margin: 0 0 8px;
      font-size: 1rem;
      font-family: "Sora", "Work Sans", sans-serif;
    }
    .stats {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .stat {
      border-radius: 10px;
      border: 1px solid;
      padding: 8px;
    }
    body.v1 .stat { border-color: #bed2ec; background: #f6faff; }
    body.v2 .stat { border-color: #3f5a7f; background: #101a2b; }
    .stat .k { font-size: 0.75rem; opacity: 0.82; }
    .stat .v { margin-top: 4px; font-weight: 700; }
    .info, .status {
      border-radius: 10px;
      border: 1px solid;
      padding: 10px;
      white-space: pre-wrap;
      font-size: 0.86rem;
      line-height: 1.4;
      min-height: 86px;
    }
    body.v1 .info, body.v1 .status { border-color: #bfd2ea; background: #f8fbff; }
    body.v2 .info, body.v2 .status { border-color: #3d5678; background: #111b2c; }
    .status.good { color: __GOOD_COLOR__; }
    .status.bad { color: var(--bad); }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body class="__BODY_CLASS__">
  <div class="wrap">
    <header class="top">
      <div class="brand">
        <span class="brand-mark">NX</span>
        <span>__TITLE__</span>
      </div>
      <span class="tag">__STAGE__</span>
    </header>

    <section class="hero">
      <h1>Easy Operator View</h1>
      <p>__SUBTITLE__</p>
      <span class="banner">__BANNER__</span>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="controls">
          <button id="refresh">Reload Catalog</button>
          <button id="buy">Run Checkout</button>
          <button id="bundle">Run Checkout x3</button>
          <button id="addMock" class="secondary">Add All To Cart</button>
        </div>
        <div id="items" class="grid"></div>
      </div>

      <aside class="panel">
        <h2>Product Details</h2>
        <div id="productInfo" class="info">Select a product card to call /product/&lt;sku&gt;.</div>
        <h2 style="margin-top:10px">Activity</h2>
        <div id="status" class="status good">Ready.</div>
        <div class="stats">
          <div class="stat"><div class="k">Cart</div><div id="cartCount" class="v">0</div></div>
          <div class="stat"><div class="k">Checkouts</div><div id="orderCount" class="v">0</div></div>
        </div>
      </aside>
    </section>
  </div>

  <script>
    const itemsEl = document.getElementById("items");
    const statusEl = document.getElementById("status");
    const productInfoEl = document.getElementById("productInfo");
    const cartCountEl = document.getElementById("cartCount");
    const orderCountEl = document.getElementById("orderCount");

    let cartCount = 0;
    let orderCount = 0;

    const productMeta = {
      "sku-1": { category: "Apparel", comparePrice: 64, note: "Best seller hoodie" },
      "sku-2": { category: "Drinkware", comparePrice: 18, note: "Daily desk mug" },
      "sku-3": { category: "Accessories", comparePrice: 10, note: "Sticker set" }
    };

    function thumbStyle(id) {
      const palette = {
        "sku-1": "linear-gradient(140deg, #3a54cc, #67a6ff)",
        "sku-2": "linear-gradient(140deg, #118876, #4fcfb8)",
        "sku-3": "linear-gradient(140deg, #c66325, #ffac66)"
      };
      return palette[id] || "linear-gradient(140deg, #4f6488, #738fb9)";
    }

    function setStatus(text, ok = true) {
      statusEl.textContent = text;
      statusEl.className = "status " + (ok ? "good" : "bad");
    }

    function renderProductInfo(payload) {
      const item = payload.item || {};
      const recs = payload.recommendations || [];
      const recLine = recs.length ? recs.map((r) => r.id).join(", ") : "none";
      productInfoEl.textContent =
        `sku=${item.id || "n/a"}\n` +
        `name=${item.name || "n/a"}\n` +
        `price=$${Number(item.price || 0).toFixed(2)}\n` +
        `source=${payload.source || "n/a"}\n` +
        `path=${payload.path || "n/a"}\n` +
        `recommendations=${recLine}`;
    }

    async function viewProduct(it) {
      try {
        const resp = await fetch(`/product/${it.id}`, { method: "GET" });
        const body = await resp.json();
        renderProductInfo(body);
        setStatus(`Viewed product page for ${it.id}. Product-page traffic generated.`, true);
      } catch (err) {
        setStatus("Product detail load failed: " + err, false);
      }
    }

    function renderItem(it) {
      const meta = productMeta[it.id] || { category: "General", comparePrice: Number(it.price) + 10, note: "Store item" };
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <div class="thumb" style="background:${thumbStyle(it.id)}">
          <span>${meta.category}</span>
          <span class="sku">${it.id}</span>
        </div>
        <h3 class="name">${it.name}</h3>
        <p class="meta">${meta.note}</p>
        <div class="row">
          <div class="price">$${Number(it.price).toFixed(2)}</div>
          <div>
            <button class="small viewBtn">View</button>
            <button class="small addBtn">Add</button>
          </div>
        </div>
      `;
      card.querySelector(".thumb").addEventListener("click", () => viewProduct(it));
      card.querySelector(".viewBtn").addEventListener("click", () => viewProduct(it));
      card.querySelector(".addBtn").addEventListener("click", () => {
        cartCount += 1;
        cartCountEl.textContent = String(cartCount);
        setStatus(`Added ${it.id} to cart.`);
      });
      return card;
    }

    async function loadCatalog() {
      try {
        const resp = await fetch("/catalog", { method: "GET" });
        const items = await resp.json();
        itemsEl.innerHTML = "";
        items.forEach((it) => itemsEl.appendChild(renderItem(it)));
        setStatus("Catalog loaded. Use View to generate product-page traffic.");
      } catch (err) {
        setStatus("Catalog load failed: " + err, false);
      }
    }

    async function checkout(multiplier) {
      const runs = Number(multiplier || 1);
      let okRuns = 0;
      try {
        for (let i = 0; i < runs; i += 1) {
          const orderId = "order-" + Date.now() + "-" + i;
          const resp = await fetch("/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: orderId, user: "demo-user" })
          });
          if (resp.ok) {
            okRuns += 1;
          }
          orderCount += 1;
          orderCountEl.textContent = String(orderCount);
        }
        setStatus(`Checkout run completed: success=${okRuns}/${runs}`, okRuns === runs);
      } catch (err) {
        setStatus("Checkout failed: " + err, false);
      }
    }

    document.getElementById("refresh").addEventListener("click", loadCatalog);
    document.getElementById("buy").addEventListener("click", () => checkout(1));
    document.getElementById("bundle").addEventListener("click", () => checkout(3));
    document.getElementById("addMock").addEventListener("click", () => {
      cartCount += 3;
      cartCountEl.textContent = String(cartCount);
      setStatus("Added all products to cart.");
    });
    loadCatalog();
  </script>
</body>
</html>
"""
    html = (
        template
        .replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__BODY_CLASS__", body_class)
        .replace("__STAGE__", stage)
        .replace("__BANNER__", banner)
        .replace("__GOOD_COLOR__", "var(--v2-good)" if is_v2 else "var(--v1-good)")
    )
    return html, version


def register(app):
    catalog_url = os.getenv("CATALOG_URL", "http://catalog-api.demo-app.svc.cluster.local")
    checkout_url = os.getenv("CHECKOUT_URL", "http://checkout-api.demo-app.svc.cluster.local")

    @app.route("/", methods=["GET"])
    def index():
        version = os.getenv("SERVICE_VERSION", "unknown")
        html, frontend_version = _render_frontend(version)
        return html, 200, {
            "Content-Type": "text/html; charset=utf-8",
            "X-Frontend-Version": frontend_version,
        }

    @app.route("/catalog", methods=["GET"])
    def frontend_catalog():
        resp = requests.get(f"{catalog_url}/items", timeout=5)
        return jsonify(resp.json()), resp.status_code

    @app.route("/product/<item_id>", methods=["GET"])
    def frontend_product(item_id):
        resp = requests.get(f"{catalog_url}/items", timeout=5)
        items = resp.json()
        item = next((i for i in items if i.get("id") == item_id), None)
        if item is None:
            return jsonify({"error": "not_found", "item_id": item_id}), 404

        recs = [i for i in items if i.get("id") != item_id][:2]
        return jsonify({
            "item": item,
            "recommendations": recs,
            "source": "catalog-api",
            "path": "frontend -> catalog-api (/items) -> frontend (/product)",
        })

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
