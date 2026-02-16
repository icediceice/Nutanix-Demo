import os

import requests
from flask import jsonify, request


def _render_frontend(version: str) -> tuple[str, str]:
    is_v2 = version.startswith("v2")
    title = "Nutanix Storefront v2 (Canary Candidate)" if is_v2 else "Nutanix Storefront v1 (Stable)"
    subtitle = (
        "Next-gen merchandising and faster story beats. This look should increase as canary traffic shifts to v2."
        if is_v2
        else "Stable experience. This look should dominate when traffic stays on v1."
    )
    campaign = "Canary Spotlight" if is_v2 else "Proven Baseline"
    tone = "Experimental journey active" if is_v2 else "Trusted journey active"
    body_class = "v2" if is_v2 else "v1"
    version_wall = "LIVE VERSION: v2 CANDIDATE" if is_v2 else "LIVE VERSION: v1 STABLE"
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Archivo+Expanded:wght@600;700;800&family=Work+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --v1-bg-1: #f3f7fd;
      --v1-bg-2: #dce7f6;
      --v1-ink: #1a2a3f;
      --v1-soft: #5b6f8f;
      --v1-card: #ffffff;
      --v1-line: #bfd0e8;
      --v1-accent: #005dc4;
      --v1-hero: #0e4d92;
      --v1-good: #0b9f74;
      --v1-badge: #ecf4ff;

      --v2-bg-1: #121826;
      --v2-bg-2: #09101a;
      --v2-ink: #eff4ff;
      --v2-soft: #b8c8e8;
      --v2-card: #151f31;
      --v2-line: #2c3a56;
      --v2-accent: #ff7f32;
      --v2-hero: #ffd3b5;
      --v2-good: #2dd2ac;
      --v2-badge: #11192a;

      --danger: #d64545;
      --radius-xl: 20px;
      --radius-lg: 14px;
      --radius-sm: 10px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Work Sans", "Segoe UI", sans-serif;
      min-height: 100vh;
    }}
    body.v1 {{
      color: var(--v1-ink);
      background: radial-gradient(circle at 15% 10%, #ffffff 0%, var(--v1-bg-1) 35%, var(--v1-bg-2) 100%);
    }}
    body.v2 {{
      color: var(--v2-ink);
      background: radial-gradient(circle at 10% 10%, #202f49, var(--v2-bg-1) 40%, var(--v2-bg-2) 100%);
    }}
    .wrap {{ max-width: 1120px; margin: 22px auto 40px; padding: 0 16px; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
    }}
    .brand-mark {{
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      font-size: 0.9rem;
      font-weight: 800;
      letter-spacing: 0.06em;
      color: #fff;
    }}
    body.v1 .brand-mark {{ background: linear-gradient(145deg, #005dc4, #34a1ff); }}
    body.v2 .brand-mark {{ background: linear-gradient(145deg, #ff7f32, #ffb365); color: #2b1c12; }}
    .brand-text {{
      font-family: "Archivo Expanded", "Work Sans", sans-serif;
      letter-spacing: 0.04em;
      font-size: 0.95rem;
      text-transform: uppercase;
    }}
    .top-pills {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .version-wall {{
      border-radius: var(--radius-lg);
      padding: 12px 14px;
      margin-bottom: 14px;
      text-align: center;
      font-weight: 900;
      font-size: clamp(1rem, 2.3vw, 1.8rem);
      letter-spacing: .06em;
      text-transform: uppercase;
      animation: pulse 1.8s ease-in-out infinite;
      font-family: "Archivo Expanded", "Work Sans", sans-serif;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(1); }}
      50% {{ transform: scale(1.015); }}
      100% {{ transform: scale(1); }}
    }}
    body.v1 .version-wall {{
      color: #003a79;
      background: linear-gradient(90deg, #dbeeff, #eff6ff);
      border: 2px solid #8ac2ff;
      box-shadow: 0 10px 22px rgba(32, 102, 192, 0.15);
    }}
    body.v2 .version-wall {{
      color: #fff2e8;
      background: linear-gradient(90deg, #ff7f32, #ffbb76);
      border: 2px solid #ffd1a8;
      box-shadow: 0 12px 26px rgba(255, 127, 50, 0.34);
    }}
    .hero {{
      border-radius: var(--radius-xl);
      padding: 20px;
      margin-bottom: 16px;
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 14px;
    }}
    body.v1 .hero {{ background: linear-gradient(155deg, #ffffff, #f5f9ff); border: 1px solid var(--v1-line); }}
    body.v2 .hero {{ background: linear-gradient(155deg, #1a2640, #141d2f); border: 1px solid var(--v2-line); box-shadow: 0 16px 34px rgba(0,0,0,.28); }}
    .kicker {{
      margin: 0 0 10px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.74rem;
      font-weight: 700;
    }}
    body.v1 .kicker {{ color: #406999; }}
    body.v2 .kicker {{ color: #ffc89f; }}
    .title {{
      margin: 0;
      font-family: "Archivo Expanded", "Work Sans", sans-serif;
      font-size: clamp(1.55rem, 2.4vw, 2.1rem);
      line-height: 1.2;
    }}
    .subtitle {{
      margin: 10px 0 0;
      font-size: 1rem;
      line-height: 1.45;
    }}
    body.v1 .subtitle {{ color: var(--v1-soft); }}
    body.v2 .subtitle {{ color: var(--v2-soft); }}
    .hero-actions {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      margin: 16px 0 0;
    }}
    .mission {{
      border-radius: var(--radius-lg);
      padding: 14px;
      align-self: stretch;
      display: grid;
      gap: 10px;
      border: 1px dashed;
    }}
    body.v1 .mission {{ border-color: #9ab8dd; background: #edf5ff; }}
    body.v2 .mission {{ border-color: #516891; background: #111a2a; }}
    .mission h2 {{
      margin: 0;
      font-size: 1.02rem;
    }}
    .mission p {{
      margin: 0;
      font-size: 0.9rem;
      line-height: 1.4;
    }}
    .mission-stats {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }}
    .mini {{
      border-radius: 10px;
      padding: 8px 10px;
      border: 1px solid;
    }}
    body.v1 .mini {{ border-color: #b8cee9; background: #fff; }}
    body.v2 .mini {{ border-color: #344a6f; background: #18253b; }}
    .mini .k {{ font-size: 0.74rem; opacity: 0.8; }}
    .mini .v {{ font-size: 1rem; font-weight: 700; margin-top: 4px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin: 14px 0;
    }}
    .card {{
      border-radius: var(--radius-lg);
      padding: 12px;
      overflow: hidden;
      transition: transform .2s ease, box-shadow .2s ease;
    }}
    body.v1 .card {{ background: var(--v1-card); border: 1px solid var(--v1-line); }}
    body.v2 .card {{ background: #16233a; border: 1px solid #2d4061; }}
    .card:hover {{
      transform: translateY(-3px);
    }}
    body.v1 .card:hover {{ box-shadow: 0 12px 24px rgba(33, 93, 171, 0.14); }}
    body.v2 .card:hover {{ box-shadow: 0 14px 26px rgba(0, 0, 0, 0.3); }}
    .thumb {{
      border-radius: 10px;
      min-height: 130px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      padding: 10px;
      margin-bottom: 10px;
      color: #fff;
      font-weight: 700;
      letter-spacing: 0.03em;
    }}
    .sku {{
      font-size: 0.78rem;
      opacity: 0.92;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 999px;
      padding: 4px 8px;
      font-weight: 600;
    }}
    .name {{
      margin: 0;
      font-size: 1.04rem;
      line-height: 1.35;
    }}
    .meta {{
      margin-top: 6px;
      font-size: 0.84rem;
      opacity: 0.84;
      min-height: 34px;
    }}
    .row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 10px;
      gap: 8px;
    }}
    .price {{ font-weight: 800; font-size: 1.08rem; }}
    .strike {{
      font-size: 0.82rem;
      text-decoration: line-through;
      opacity: 0.7;
      margin-left: 6px;
    }}
    .badge {{
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 0.74rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 700;
    }}
    body.v1 .badge {{ background: var(--v1-badge); border: 1px solid #bad2ef; color: #355881; }}
    body.v2 .badge {{ background: var(--v2-badge); border: 1px solid #3b5276; color: #bfd4f6; }}
    .actions {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      margin: 10px 0 0;
    }}
    button {{
      border: none;
      border-radius: var(--radius-sm);
      padding: 10px 13px;
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      font-family: "Work Sans", sans-serif;
      transition: transform .15s ease, filter .15s ease;
    }}
    button:hover {{ transform: translateY(-1px); filter: brightness(1.06); }}
    body.v1 button {{ background: var(--v1-accent); }}
    body.v2 button {{ background: var(--v2-accent); color: #2b1b0e; }}
    button.secondary {{ background: #516d8c !important; }}
    button.ghost {{
      background: transparent !important;
      border: 1px solid;
    }}
    body.v1 button.ghost {{ color: #355881; border-color: #9bb8df; }}
    body.v2 button.ghost {{ color: #c8daf8; border-color: #3f5579; }}
    .pill {{
      border-radius: 999px;
      padding: 6px 10px;
      font-size: .85rem;
    }}
    body.v1 .pill {{ border: 1px solid var(--v1-line); background: #fff; color: #365983; }}
    body.v2 .pill {{ border: 1px solid #3d5578; background: #101a2b; color: #d8e6ff; }}
    .insight-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
      margin-top: 12px;
    }}
    .panel {{
      border-radius: var(--radius-lg);
      padding: 14px;
      border: 1px solid;
    }}
    body.v1 .panel {{ background: #fff; border-color: #bfd1ea; }}
    body.v2 .panel {{ background: #101b2c; border-color: #2c4061; }}
    .panel h3 {{
      margin: 0 0 8px;
      font-size: 1rem;
    }}
    .story {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 8px;
    }}
    .story li {{
      border-radius: 10px;
      padding: 8px 10px;
      border: 1px solid;
      font-size: 0.88rem;
    }}
    body.v1 .story li {{ border-color: #c6d8ee; background: #f6faff; }}
    body.v2 .story li {{ border-color: #344a6d; background: #15233a; }}
    .status {{
      margin-top: 10px;
      padding: 10px;
      border-radius: var(--radius-sm);
      font-size: .9rem;
      white-space: pre-wrap;
      min-height: 108px;
    }}
    body.v1 .status {{ background: #fff; border: 1px solid var(--v1-line); }}
    body.v2 .status {{ background: #0f1727; border: 1px solid #324768; }}
    body.v1 .ok {{ color: var(--v1-good); }}
    body.v2 .ok {{ color: var(--v2-good); }}
    .bad {{ color: var(--danger); }}
    code {{ padding: 2px 5px; border-radius: 5px; }}
    body.v1 code {{ background: #eef5ff; }}
    body.v2 code {{ background: #1f2e47; color: #dce9ff; }}
    @media (max-width: 860px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body class="__BODY_CLASS__">
  <div class="wrap">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark">NX</span>
        <span class="brand-text">Nutanix Marketline</span>
      </div>
      <div class="top-pills">
        <span class="pill">Campaign: __CAMPAIGN__</span>
        <span class="pill">Theme: __TONE__</span>
        <span class="pill">Frontend: __VERSION__</span>
      </div>
    </header>

    <section class="version-wall">__VERSION_WALL__</section>
    <section class="hero">
      <div>
        <p class="kicker">Story Mode</p>
        <h1 class="title">__TITLE__</h1>
        <p class="subtitle">__SUBTITLE__</p>
        <div class="hero-actions">
          <span class="pill">Objective: convert browsing into checkout flow</span>
          <span class="pill">Path under test: <code>/checkout</code></span>
          <span class="pill">Release narrative: v1 reliability vs v2 conversion lift</span>
        </div>
      </div>
      <aside class="mission">
        <h2>Operator Mission</h2>
        <p>Watch this page while shifting canary weight. The visuals make version changes obvious while traces confirm request path health.</p>
        <div class="mission-stats">
          <div class="mini"><div class="k">Cart Size</div><div id="cartCount" class="v">0</div></div>
          <div class="mini"><div class="k">Checkouts</div><div id="orderCount" class="v">0</div></div>
          <div class="mini"><div class="k">Flow</div><div class="v">catalog -> checkout -> payment</div></div>
          <div class="mini"><div class="k">Status</div><div id="flowStatus" class="v">warming</div></div>
        </div>
      </aside>
    </section>

    <div id="items" class="grid"></div>

    <section class="panel">
      <div class="actions">
        <button id="buy">Run Single Checkout</button>
        <button id="bundle">Run Flash Sale x3</button>
        <button id="refresh" class="secondary">Reload Catalog</button>
        <button id="addMock" class="ghost">Add All To Cart</button>
      </div>
      <div id="status" class="status">Ready.</div>
    </section>

    <section class="insight-grid">
      <article class="panel">
        <h3>Journey Timeline</h3>
        <ol id="story" class="story">
          <li>Catalog not loaded yet.</li>
        </ol>
      </article>
      <article class="panel">
        <h3>Product Detail Traffic</h3>
        <ol id="productStory" class="story">
          <li>Open a product card to call <code>/product/&lt;sku&gt;</code>.</li>
        </ol>
      </article>
      <article class="panel">
        <h3>Narrative Notes</h3>
        <ul class="story">
          <li>Browse traffic should dominate in baseline load tests.</li>
          <li>Checkout calls should still produce traces across all services.</li>
          <li>Use Kiali + Jaeger to compare v1/v2 customer paths.</li>
        </ul>
      </article>
    </section>
  </div>

  <script>
    const itemsEl = document.getElementById("items");
    const statusEl = document.getElementById("status");
    const storyEl = document.getElementById("story");
    const productStoryEl = document.getElementById("productStory");
    const cartCountEl = document.getElementById("cartCount");
    const orderCountEl = document.getElementById("orderCount");
    const flowStatusEl = document.getElementById("flowStatus");

    let cartCount = 0;
    let orderCount = 0;

    const productMeta = {{
      "sku-1": {{ category: "apparel", highlight: "Fan favorite", comparePrice: 64 }},
      "sku-2": {{ category: "drinkware", highlight: "Desk essential", comparePrice: 18 }},
      "sku-3": {{ category: "stickers", highlight: "Fast-moving", comparePrice: 10 }}
    }};

    function thumbStyle(id) {{
      const map = {{
        "sku-1": "linear-gradient(140deg, #354dbf, #61a1ff)",
        "sku-2": "linear-gradient(140deg, #0b8a79, #4cc7b3)",
        "sku-3": "linear-gradient(140deg, #cc5f1f, #ffa45d)"
      }};
      return map[id] || "linear-gradient(140deg, #3f557a, #6d89b3)";
    }}

    function setStatus(text, ok=true) {{
      statusEl.textContent = text;
      statusEl.className = "status " + (ok ? "ok" : "bad");
    }}

    function setFlowStatus(value) {{
      flowStatusEl.textContent = value;
    }}

    function pushStory(lines) {{
      storyEl.innerHTML = "";
      lines.forEach((line) => {{
        const li = document.createElement("li");
        li.textContent = line;
        storyEl.appendChild(li);
      }});
    }}

    function pushProductStory(lines) {{
      productStoryEl.innerHTML = "";
      lines.forEach((line) => {{
        const li = document.createElement("li");
        li.innerHTML = line;
        productStoryEl.appendChild(li);
      }});
    }}

    async function viewProduct(it) {{
      try {{
        const resp = await fetch(`/product/${it.id}`, {{ method: "GET" }});
        const body = await resp.json();
        const item = body.item || it;
        const recs = body.recommendations || [];
        pushProductStory([
          `sku=${item.id} name=${item.name}`,
          `price=$${Number(item.price).toFixed(2)} source=${body.source || "frontend"}`,
          `path=${body.path || "frontend -> catalog-api"}`,
          `recs=${recs.map((r) => r.id).join(", ") || "none"}`
        ]);
        setFlowStatus("product-view");
        setStatus(`Product page viewed for ${item.name}. Product-detail traffic generated.`);
      }} catch (err) {{
        setFlowStatus("product-error");
        setStatus("Product detail load failed: " + err, false);
      }}
    }}

    function renderItem(it) {{
      const meta = productMeta[it.id] || {{ category: "general", highlight: "Standard", comparePrice: Number(it.price) + 10 }};
      const card = document.createElement("article");
      card.className = "card";
      card.innerHTML = `
        <div class="thumb" style="background:${thumbStyle(it.id)}">
          <span>${meta.highlight}</span>
          <span class="sku">${it.id}</span>
        </div>
        <span class="badge">${meta.category}</span>
        <h3 class="name">${it.name}</h3>
        <p class="meta">Limited demo drop tuned for observability storylines.</p>
        <div class="row">
          <div>
            <span class="price">$${Number(it.price).toFixed(2)}</span>
            <span class="strike">$${Number(meta.comparePrice).toFixed(2)}</span>
          </div>
          <button class="ghost viewOne">View</button>
          <button class="ghost addOne">Add</button>
        </div>
      `;
      card.querySelector(".viewOne").addEventListener("click", () => {{
        viewProduct(it);
      }});
      card.querySelector(".thumb").addEventListener("click", () => {{
        viewProduct(it);
      }});
      card.querySelector(".addOne").addEventListener("click", () => {{
        cartCount += 1;
        cartCountEl.textContent = String(cartCount);
        setFlowStatus("browsing");
        setStatus(`Added ${it.name} to local cart simulation.`, true);
      }});
      return card;
    }}

    async function loadCatalog() {{
      try {{
        const resp = await fetch("/catalog", {{ method: "GET" }});
        const items = await resp.json();
        itemsEl.innerHTML = "";
        items.forEach((it) => itemsEl.appendChild(renderItem(it)));
        setFlowStatus("catalog-ready");
        pushStory([
          "Catalog loaded from catalog-api.",
          "Open product cards to generate /product/<sku> traffic.",
          "Then run checkout to generate full service chain traces.",
          "Switch canary percentages to compare visual conversion story."
        ]);
        pushProductStory([
          "Catalog is ready.",
          "Click a card to generate product-view traffic and details."
        ]);
        setStatus("Catalog loaded. Use checkout actions to drive storyline traffic.");
      }} catch (err) {{
        setFlowStatus("catalog-error");
        setStatus("Catalog load failed: " + err, false);
      }}
    }}

    async function checkout(multiplier) {{
      const runs = Number(multiplier || 1);
      let okRuns = 0;
      try {{
        for (let i = 0; i < runs; i += 1) {{
          const orderId = "order-" + Date.now() + "-" + i;
          const resp = await fetch("/checkout", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ order_id: orderId, user: "demo-user" }})
          }});
          const body = await resp.json();
          const traceId = resp.headers.get("X-Trace-Id") || "n/a";
          const frontendVersion = resp.headers.get("X-Frontend-Version") || "__VERSION__";
          const paymentStatus = (((body || {{}}).result || {{}}).payment || {{}}).status || "unknown";
          if (resp.ok) {{
            okRuns += 1;
          }}
          orderCount += 1;
          orderCountEl.textContent = String(orderCount);
          setFlowStatus(resp.ok ? "checkout-ok" : "checkout-degraded");
          pushStory([
            `order_id=${orderId}`,
            `frontend=${frontendVersion}`,
            `trace_id=${traceId}`,
            `payment_status=${paymentStatus}`,
            "service_path=frontend -> catalog-api -> checkout-api -> payment-mock"
          ]);
        }}
        const allOk = okRuns === runs;
        setStatus(
          `checkouts=${runs}\\nsuccess=${okRuns}\\ncart_items=${cartCount}\\npath=frontend->catalog-api->checkout-api->payment-mock`,
          allOk
        );
      }} catch (err) {{
        setFlowStatus("checkout-error");
        setStatus("Checkout failed: " + err, false);
      }}
    }}

    document.getElementById("buy").addEventListener("click", () => checkout(1));
    document.getElementById("bundle").addEventListener("click", () => checkout(3));
    document.getElementById("refresh").addEventListener("click", loadCatalog);
    document.getElementById("addMock").addEventListener("click", () => {{
      cartCount += 3;
      cartCountEl.textContent = String(cartCount);
      setFlowStatus("cart-warm");
      setStatus("Added entire catalog to local cart simulation.");
    }});
    loadCatalog();
  </script>
</body>
</html>
"""
    html = (
        template
        .replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__CAMPAIGN__", campaign)
        .replace("__TONE__", tone)
        .replace("__BODY_CLASS__", body_class)
        .replace("__VERSION__", version)
        .replace("__VERSION_WALL__", version_wall)
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
