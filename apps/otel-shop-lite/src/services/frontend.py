import os

import requests
from flask import jsonify, request


def _render_frontend(version: str) -> tuple[str, str]:
    is_v2 = version.startswith("v2")
    title = "Nutanix Storefront"
    subtitle = "Browse the catalog, view product pages, and run checkout — every click generates real traces."
    body_class = "v2" if is_v2 else "v1"
    stage = "v2 \u00b7 Canary" if is_v2 else "v1 \u00b7 Stable"
    banner = "NKP CANARY" if is_v2 else "NKP RELEASE"
    jaeger_url = os.getenv("JAEGER_QUERY_URL", "")
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500&display=swap" rel="stylesheet">
  <style>
    /* ─── Nutanix Brand Tokens ─── */
    :root {
      /* Official Nutanix palette */
      --nx-blue:      #0091DA;   /* Nutanix Primary Blue  */
      --nx-blue-dk:   #024DA0;   /* Endeavour Deep Blue   */
      --nx-green:     #AFD135;   /* Atlantis — the X mark */
      --nx-navy:      #003B5C;   /* Dark Navy             */
      --nx-navy-md:   #00243A;
      --nx-navy-lt:   #004A72;

      /* v1 — Dark / Stable Release — Blue-accent */
      --v1-bg:       #001828;
      --v1-surface:  #002238;
      --v1-raised:   #002E4C;
      --v1-border:   #004070;
      --v1-ink:      #D8E8F8;
      --v1-muted:    #6090B8;
      --v1-cta:      #0091DA;
      --v1-good:     #3AB4F0;   /* blue highlight for status on v1 */
      --v1-bad:      #FF5252;

      /* v2 — Dark / Canary Release */
      --v2-bg:       #00182C;
      --v2-surface:  #00243A;
      --v2-raised:   #003050;
      --v2-border:   #004068;
      --v2-ink:      #DDE9F6;
      --v2-muted:    #6A9AB8;
      --v2-cta:      #0091DA;
      --v2-good:     #AFD135;   /* full Atlantis on dark bg  */
      --v2-bad:      #FF5252;
    }

    /* ─── Reset ─── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "DM Sans", "Segoe UI", sans-serif;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }
    button { font-family: inherit; cursor: pointer; }

    /* ─── Theme bodies ─── */
    body.v1 { background: var(--v1-bg); color: var(--v1-ink); }
    body.v2 { background: var(--v2-bg); color: var(--v2-ink); }

    /* v1 uses Nutanix Blue as its signature accent */
    body.v1 .hero-eyebrow  { color: var(--nx-blue); }
    body.v1 .hero-eyebrow::before { background: var(--nx-blue); }
    body.v1 .section-eye   { color: var(--nx-blue); }
    body.v1 .footer-stage  { color: var(--nx-blue); }
    /* v2 uses Atlantis green as its signature accent — stays as default */

    /* ─── Sticky header ─── */
    .site-header {
      position: sticky; top: 0; z-index: 200;
      height: 62px;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 32px;
      border-bottom: 1px solid;
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
    }
    body.v1 .site-header { background: rgba(0,24,40,.92); border-color: var(--v1-border); }
    body.v2 .site-header { background: rgba(0,16,24,.92); border-color: var(--v2-border); }

    .h-brand { display: flex; align-items: center; gap: 10px; }

    /* Brand mark — Atlantis green, navy text = instantly Nutanix */
    .brand-mark {
      width: 34px; height: 34px;
      border-radius: 8px;
      display: grid; place-items: center;
      background: var(--nx-green);
      color: var(--nx-navy);
      font-family: "Rubik", sans-serif;
      font-size: 0.8rem; font-weight: 700;
      flex-shrink: 0; letter-spacing: 0.02em;
    }
    .brand-name {
      font-family: "Rubik", sans-serif;
      font-size: 1rem; font-weight: 600;
      letter-spacing: 0.01em;
    }
    .brand-pill {
      padding: 3px 10px;
      border-radius: 99px;
      font-size: 0.65rem; font-weight: 700;
      letter-spacing: 0.1em; text-transform: uppercase;
      border: 1px solid;
    }
    body.v1 .brand-pill { color: var(--nx-blue);    border-color: #005A8A; background: #002440; }
    body.v2 .brand-pill { color: var(--nx-green);   border-color: #005A8A; background: #002840; }

    .h-counters { display: flex; align-items: center; gap: 22px; }
    .h-counter { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; }
    body.v1 .h-counter { color: var(--v1-muted); }
    body.v2 .h-counter { color: var(--v2-muted); }
    .h-icon { opacity: .5; }
    .h-num {
      font-weight: 700; font-size: 0.88rem;
      transition: transform .2s cubic-bezier(.34,1.56,.64,1);
      display: inline-block;
    }
    body.v1 .h-num { color: var(--v1-ink); }
    body.v2 .h-num { color: var(--v2-ink); }
    .h-num.bump { transform: scale(1.55); }

    /* ─── Hero ─── */
    .hero {
      max-width: 1240px; margin: 0 auto;
      padding: 52px 32px 38px;
      display: grid; grid-template-columns: 1fr auto;
      gap: 24px; align-items: end;
    }
    .hero-eyebrow {
      display: inline-flex; align-items: center; gap: 8px;
      font-size: 0.68rem; font-weight: 700;
      letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--nx-green);
      margin-bottom: 14px;
    }
    /* Nutanix Atlantis accent bar */
    .hero-eyebrow::before {
      content: "";
      display: block;
      width: 18px; height: 3px;
      background: var(--nx-green);
      border-radius: 2px;
      flex-shrink: 0;
    }
    .hero-heading {
      font-family: "Rubik", sans-serif;
      font-size: clamp(2.4rem, 5vw, 3.9rem);
      font-weight: 700;
      line-height: 1.05;
      letter-spacing: -0.02em;
    }
    .hero-sub {
      margin-top: 14px;
      font-size: 0.9rem; line-height: 1.65;
      max-width: 460px;
    }
    body.v1 .hero-sub { color: var(--v1-muted); }
    body.v2 .hero-sub { color: var(--v2-muted); }
    .hero-ctas { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }

    /* ─── Buttons ─── */
    .btn {
      border: none; border-radius: 8px;
      font-family: "Rubik", sans-serif;
      font-weight: 600; font-size: 0.85rem;
      padding: 11px 22px; letter-spacing: 0.01em;
      transition: transform .12s ease, box-shadow .12s ease;
    }
    .btn:active { transform: scale(0.96) !important; }
    /* Nutanix Blue primary */
    .btn-primary {
      background: var(--nx-blue); color: #fff;
      box-shadow: 0 2px 12px rgba(0,145,218,.3);
    }
    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 5px 20px rgba(0,145,218,.45);
    }
    .btn-ghost {
      background: transparent; border: 1px solid;
    }
    body.v1 .btn-ghost { color: var(--v1-muted); border-color: var(--v1-border); }
    body.v1 .btn-ghost:hover { color: #fff; border-color: var(--nx-blue); background: rgba(0,145,218,.15); }
    body.v2 .btn-ghost { color: var(--v2-muted); border-color: var(--v2-border); }
    body.v2 .btn-ghost:hover { color: var(--nx-green); border-color: var(--nx-green); background: rgba(175,209,53,.08); }

    /* ─── Store layout ─── */
    .store-wrap {
      display: grid; grid-template-columns: 1fr 296px;
      gap: 24px; max-width: 1240px;
      margin: 0 auto; padding: 0 32px 64px;
    }
    .section-eye {
      font-size: 0.65rem; font-weight: 700;
      letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--nx-green); margin-bottom: 16px;
    }

    /* ─── Product grid ─── */
    .product-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 20px;
    }

    /* ─── Product card ─── */
    .pcard {
      border-radius: 14px; border: 1px solid;
      overflow: hidden; display: flex; flex-direction: column;
      transition: transform .22s cubic-bezier(.34,1.1,.64,1), box-shadow .22s ease;
    }
    body.v1 .pcard { border-color: var(--v1-border); background: var(--v1-surface); }
    body.v2 .pcard { border-color: var(--v2-border); background: var(--v2-surface); }
    .pcard:hover { transform: translateY(-5px); }
    body.v1 .pcard:hover { box-shadow: 0 14px 44px rgba(0,59,92,.1); }
    body.v2 .pcard:hover { box-shadow: 0 14px 44px rgba(0,0,0,.5); }

    .pcard-art {
      position: relative; height: 188px;
      display: flex; align-items: center; justify-content: center;
      cursor: pointer; overflow: hidden;
    }
    /* Atlantis accent stripe at bottom of art */
    .pcard-art::before {
      content: ""; position: absolute;
      bottom: 0; left: 0; right: 0; height: 3px;
      background: var(--nx-green);
      z-index: 2;
    }
    .pcard-art::after {
      content: ""; position: absolute; inset: 0;
      background: rgba(0,0,0,0); transition: background .2s;
    }
    .pcard:hover .pcard-art::after { background: rgba(0,0,0,.07); }
    .pcard-art-svg {
      position: relative; z-index: 1;
      transition: transform .3s cubic-bezier(.34,1.2,.64,1);
      filter: drop-shadow(0 6px 18px rgba(0,0,0,.25));
    }
    .pcard:hover .pcard-art-svg { transform: scale(1.07) translateY(-4px); }

    .pcard-cat {
      position: absolute; top: 12px; left: 12px; z-index: 3;
      font-family: "Rubik", sans-serif;
      font-size: 0.62rem; font-weight: 700;
      letter-spacing: 0.1em; text-transform: uppercase;
      color: rgba(255,255,255,.9);
      background: rgba(0,0,0,.3);
      border: 1px solid rgba(255,255,255,.22);
      border-radius: 99px; padding: 3px 9px;
      backdrop-filter: blur(4px);
    }

    .pcard-body { padding: 16px; flex: 1; display: flex; flex-direction: column; }
    .pcard-name {
      font-family: "Rubik", sans-serif;
      font-size: 1.05rem; font-weight: 600;
      line-height: 1.2; margin-bottom: 5px;
    }
    body.v1 .pcard-name { color: var(--v1-ink); }
    body.v2 .pcard-name { color: var(--v2-ink); }
    .pcard-note {
      font-size: 0.78rem; line-height: 1.45;
      margin-bottom: auto; padding-bottom: 12px;
    }
    body.v1 .pcard-note { color: var(--v1-muted); }
    body.v2 .pcard-note { color: var(--v2-muted); }

    .pcard-footer {
      display: flex; align-items: center;
      justify-content: space-between; gap: 8px;
      padding-top: 12px; border-top: 1px solid;
    }
    body.v1 .pcard-footer { border-color: var(--v1-border); }
    body.v2 .pcard-footer { border-color: var(--v2-border); }

    .pcard-price {
      font-family: "Rubik", sans-serif;
      font-size: 1.25rem; font-weight: 700;
    }
    body.v1 .pcard-price { color: var(--v1-ink); }
    body.v2 .pcard-price { color: var(--v2-ink); }

    .pcard-actions { display: flex; gap: 6px; }
    .btn-card {
      border-radius: 7px; border: 1px solid;
      font-family: "Rubik", sans-serif;
      font-size: 0.74rem; font-weight: 600;
      padding: 6px 11px; background: transparent;
      transition: all .15s; cursor: pointer;
    }
    body.v1 .btn-card.details { color: var(--v1-muted); border-color: var(--v1-border); }
    body.v1 .btn-card.details:hover { color: var(--nx-blue); border-color: var(--nx-blue); }
    body.v2 .btn-card.details { color: var(--v2-muted); border-color: var(--v2-border); }
    body.v2 .btn-card.details:hover { color: var(--nx-blue); border-color: var(--nx-blue); }
    .btn-card.add-to-bag {
      background: var(--nx-blue); color: #fff; border: none;
      box-shadow: 0 1px 6px rgba(0,145,218,.3);
    }
    .btn-card.add-to-bag:hover {
      background: #007DB8;
      box-shadow: 0 2px 10px rgba(0,145,218,.45);
    }

    /* ─── Bag panel ─── */
    .bag-panel {
      position: sticky; top: 78px; height: fit-content;
      border-radius: 14px; border: 1px solid;
      overflow: hidden;
      display: flex; flex-direction: column;
    }
    body.v1 .bag-panel { border-color: var(--v1-border); background: var(--v1-surface); }
    body.v2 .bag-panel { border-color: var(--v2-border); background: var(--v2-surface); }

    /* Atlantis accent bar top of bag panel */
    .bag-panel::before {
      content: "";
      display: block; height: 4px;
      background: var(--nx-green);
      flex-shrink: 0;
    }
    .bag-inner { padding: 18px; display: flex; flex-direction: column; gap: 14px; }

    .bag-hd { display: flex; justify-content: space-between; align-items: center; }
    .bag-title {
      font-family: "Rubik", sans-serif;
      font-size: 1.05rem; font-weight: 700;
    }
    .bag-badge {
      font-size: 0.7rem; font-weight: 600;
      padding: 3px 9px; border-radius: 99px;
    }
    body.v1 .bag-badge { background: var(--v1-raised); color: var(--v1-muted); }
    body.v2 .bag-badge { background: var(--v2-raised); color: var(--v2-muted); }

    .panel-hr { height: 1px; border: none; margin: 0 -18px; }
    body.v1 .panel-hr { background: var(--v1-border); }
    body.v2 .panel-hr { background: var(--v2-border); }

    .panel-label {
      font-family: "Rubik", sans-serif;
      font-size: 0.64rem; font-weight: 700;
      letter-spacing: 0.12em; text-transform: uppercase;
      margin-bottom: 7px;
    }
    body.v1 .panel-label { color: var(--v1-muted); }
    body.v2 .panel-label { color: var(--v2-muted); }

    .detail-box {
      border-radius: 8px; padding: 11px;
      font-size: 0.79rem; line-height: 1.65;
      white-space: pre-wrap; min-height: 80px;
    }
    body.v1 .detail-box { background: var(--v1-raised); color: var(--v1-muted); }
    body.v2 .detail-box { background: var(--v2-raised); color: var(--v2-muted); }

    .activity-box {
      border-radius: 8px; padding: 10px;
      font-size: 0.79rem; line-height: 1.5;
      min-height: 44px; transition: color .2s;
    }
    body.v1 .activity-box { background: var(--v1-raised); color: var(--v1-muted); }
    body.v2 .activity-box { background: var(--v2-raised); color: var(--v2-muted); }
    .activity-box.ok   { color: __GOOD_COLOR__; }
    body.v1 .activity-box.fail { color: var(--v1-bad); }
    body.v2 .activity-box.fail { color: var(--v2-bad); }

    /* ─── Trace badge ─── */
    .trace-badge {
      border-radius: 8px; padding: 9px 12px;
      display: none;
    }
    body.v1 .trace-badge { background: var(--v1-raised); }
    body.v2 .trace-badge { background: var(--v2-raised); }
    .trace-badge-label {
      font-size: 0.6rem; font-weight: 700;
      letter-spacing: 0.1em; text-transform: uppercase;
      margin-bottom: 5px;
    }
    body.v1 .trace-badge-label { color: var(--v1-muted); }
    body.v2 .trace-badge-label { color: var(--v2-muted); }
    .trace-id {
      display: block; font-family: monospace; font-size: 0.68rem;
      word-break: break-all; overflow-wrap: break-word;
      user-select: all; cursor: text; letter-spacing: 0.02em;
    }
    body.v1 .trace-id { color: var(--v1-muted); }
    body.v2 .trace-id { color: var(--v2-muted); }
    .trace-jaeger {
      display: block; font-size: 0.64rem; margin-top: 4px;
      opacity: 0.7; color: var(--nx-blue); text-decoration: none;
    }
    .trace-jaeger:hover { text-decoration: underline; }

    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .stat-chip { border-radius: 8px; padding: 10px 12px; text-align: center; }
    body.v1 .stat-chip { background: var(--v1-raised); }
    body.v2 .stat-chip { background: var(--v2-raised); }
    .stat-chip .sk {
      font-family: "Rubik", sans-serif;
      font-size: 0.62rem; font-weight: 700;
      letter-spacing: 0.1em; text-transform: uppercase;
    }
    body.v1 .stat-chip .sk { color: var(--v1-muted); }
    body.v2 .stat-chip .sk { color: var(--v2-muted); }
    .stat-chip .sv {
      font-family: "Rubik", sans-serif;
      font-size: 1.7rem; font-weight: 700;
      margin-top: 2px; line-height: 1;
    }
    body.v1 .stat-chip .sv { color: var(--v1-ink); }
    body.v2 .stat-chip .sv { color: var(--v2-ink); }

    .bag-cta {
      display: flex; flex-direction: column; gap: 8px;
    }
    .bag-btn-primary {
      width: 100%; border: none; border-radius: 8px;
      font-family: "Rubik", sans-serif;
      font-weight: 700; font-size: 0.86rem;
      padding: 12px; color: #fff;
      background: var(--nx-blue);
      box-shadow: 0 2px 10px rgba(0,145,218,.28);
      transition: transform .12s, box-shadow .12s;
    }
    .bag-btn-primary:active { transform: scale(0.97); }
    .bag-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 18px rgba(0,145,218,.45); }
    .bag-btn-ghost {
      width: 100%; background: transparent; border: 1px solid;
      border-radius: 8px;
      font-family: "Rubik", sans-serif;
      font-weight: 500; font-size: 0.8rem; padding: 10px;
      transition: all .15s;
    }
    body.v1 .bag-btn-ghost { color: var(--v1-muted); border-color: var(--v1-border); }
    body.v1 .bag-btn-ghost:hover { color: var(--nx-blue); border-color: var(--nx-blue); }
    body.v2 .bag-btn-ghost { color: var(--v2-muted); border-color: var(--v2-border); }
    body.v2 .bag-btn-ghost:hover { color: var(--nx-blue); border-color: var(--nx-blue); }

    /* ─── Footer ─── */
    footer {
      max-width: 1240px; margin: 0 auto;
      padding: 0 32px 36px;
      display: flex; justify-content: space-between;
      align-items: center; gap: 12px; flex-wrap: wrap;
      font-size: 0.74rem;
    }
    body.v1 footer { border-top: 1px solid var(--v1-border); color: var(--v1-muted); }
    body.v2 footer { border-top: 1px solid var(--v2-border); color: var(--v2-muted); }
    .footer-brand { display: flex; align-items: center; gap: 8px; font-weight: 500; }
    .footer-stage {
      font-family: "Rubik", sans-serif;
      font-size: 0.68rem; font-weight: 700;
      letter-spacing: 0.1em; text-transform: uppercase;
      color: var(--nx-green);
    }

    /* ─── Responsive ─── */
    @media (max-width: 960px) {
      .hero       { grid-template-columns: 1fr; padding: 36px 20px 28px; }
      .hero-ctas  { align-items: flex-start; flex-direction: row; }
      .store-wrap { grid-template-columns: 1fr; padding: 0 20px 48px; }
      .bag-panel  { position: static; }
      footer      { padding: 0 20px 28px; }
    }
    @media (max-width: 600px) {
      .site-header  { padding: 0 16px; }
      .product-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body class="__BODY_CLASS__">

  <!-- ════ HEADER ════ -->
  <header class="site-header">
    <div class="h-brand">
      <span class="brand-mark">NX</span>
      <span class="brand-name">__TITLE__</span>
      <span class="brand-pill">__BANNER__</span>
    </div>
    <div class="h-counters">
      <div class="h-counter">
        <svg class="h-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 2h1.8l2 8h7l1.5-5.2H5" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="7.2" cy="13" r=".9" fill="currentColor"/>
          <circle cx="11.8" cy="13" r=".9" fill="currentColor"/>
        </svg>
        <span id="cartCount" class="h-num">0</span>&nbsp;in bag
      </div>
      <div class="h-counter">
        <svg class="h-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2.5 8l3.8 3.8L13.5 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span id="orderCount" class="h-num">0</span>&nbsp;orders
      </div>
    </div>
  </header>

  <!-- ════ HERO ════ -->
  <section class="hero">
    <div>
      <p class="hero-eyebrow">__BANNER__</p>
      <h1 class="hero-heading">The Nutanix<br>Collection</h1>
      <p class="hero-sub">__SUBTITLE__</p>
    </div>
    <div class="hero-ctas">
      <button id="refresh" class="btn btn-primary">Refresh Collection</button>
      <button id="buy"     class="btn btn-ghost">Checkout Now</button>
    </div>
  </section>

  <!-- ════ STORE ════ -->
  <div class="store-wrap">
    <main>
      <p class="section-eye">Available Now</p>
      <div id="items" class="product-grid"></div>
    </main>

    <aside class="bag-panel">
      <div class="bag-inner">
        <div class="bag-hd">
          <h2 class="bag-title">Your Bag</h2>
          <span class="bag-badge"><span id="bagCount">0</span>&thinsp;items</span>
        </div>

        <hr class="panel-hr" />

        <div>
          <p class="panel-label">Product Detail</p>
          <div id="productInfo" class="detail-box">Tap a card to preview details.</div>
        </div>

        <hr class="panel-hr" />

        <div>
          <p class="panel-label">Activity</p>
          <div id="status" class="activity-box ok">Ready to shop.</div>
        </div>

        <div id="traceBadge" class="trace-badge">
          <p class="trace-badge-label">Last Trace</p>
          <div id="traceContent"></div>
        </div>

        <div class="stats-grid">
          <div class="stat-chip">
            <div class="sk">Bag</div>
            <div id="bagStat" class="sv">0</div>
          </div>
          <div class="stat-chip">
            <div class="sk">Orders</div>
            <div id="orderStat" class="sv">0</div>
          </div>
        </div>

        <div class="bag-cta">
          <button id="bundle" class="bag-btn-primary">Checkout &times;3</button>
          <button id="addMock" class="bag-btn-ghost">Add All to Bag</button>
        </div>
      </div>
    </aside>
  </div>

  <!-- ════ FOOTER ════ -->
  <footer>
    <div class="footer-brand">
      <span class="brand-mark" style="width:28px;height:28px;font-size:.72rem">NX</span>
      Nutanix Storefront
    </div>
    <span class="footer-stage">__STAGE__</span>
  </footer>

  <script>
    const jaegerUrl     = "__JAEGER_URL__";
    const itemsEl       = document.getElementById("items");
    const statusEl      = document.getElementById("status");
    const productInfoEl = document.getElementById("productInfo");
    const cartCountEl   = document.getElementById("cartCount");
    const orderCountEl  = document.getElementById("orderCount");
    const bagCountEl    = document.getElementById("bagCount");
    const bagStatEl     = document.getElementById("bagStat");
    const orderStatEl   = document.getElementById("orderStat");

    let cartCount  = 0;
    let orderCount = 0;
    const isV2 = document.body.classList.contains("v2");

    /* ─── Product metadata ─── */
    const productMeta = {
      "sku-1": { category: "Apparel",     note: "Premium fleece hoodie" },
      "sku-2": { category: "Drinkware",   note: "Ceramic everyday mug"  },
      "sku-3": { category: "Accessories", note: "Premium vinyl sticker set" }
    };

    /* ─── Art gradients — Nutanix Blue / Navy palette ─── */
    const artGrad = {
      "sku-1": {
        v1: "linear-gradient(145deg, #024DA0, #0091DA)",
        v2: "linear-gradient(145deg, #012060, #024DA0)"
      },
      "sku-2": {
        v1: "linear-gradient(145deg, #003B5C, #005A8A)",
        v2: "linear-gradient(145deg, #001F38, #003050)"
      },
      "sku-3": {
        v1: "linear-gradient(145deg, #1A4028, #2A6A40)",
        v2: "linear-gradient(145deg, #0C2018, #1A4028)"
      }
    };

    /* ─── Product SVG illustrations ─── */
    const productSVG = {
      "sku-1": '<svg width="96" height="88" viewBox="0 0 96 88" fill="none"><path d="M36 13 Q48 6 60 13 L75 29 L88 36 L82 57 L68 49 L68 78 L28 78 L28 49 L14 57 L8 36 L21 29 Z" fill="rgba(255,255,255,.18)" stroke="rgba(255,255,255,.75)" stroke-width="1.6" stroke-linejoin="round"/><path d="M36 13 Q48 7 60 13" stroke="rgba(255,255,255,.75)" stroke-width="2.2" fill="none" stroke-linecap="round"/><ellipse cx="48" cy="19" rx="6" ry="4" fill="rgba(255,255,255,.22)" stroke="rgba(255,255,255,.65)" stroke-width="1.3"/><line x1="34" y1="47" x2="62" y2="47" stroke="rgba(255,255,255,.2)" stroke-width="1.2" stroke-dasharray="3 3"/></svg>',
      "sku-2": '<svg width="88" height="88" viewBox="0 0 88 88" fill="none"><rect x="16" y="28" width="44" height="48" rx="8" fill="rgba(255,255,255,.18)" stroke="rgba(255,255,255,.75)" stroke-width="1.6"/><path d="M60 37 Q78 37 78 50 Q78 63 60 63" stroke="rgba(255,255,255,.65)" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M28 20 Q30 11 32 20" stroke="rgba(255,255,255,.55)" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M36 16 Q38 7 40 16" stroke="rgba(255,255,255,.55)" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M44 20 Q46 11 48 20" stroke="rgba(255,255,255,.55)" stroke-width="2" stroke-linecap="round" fill="none"/></svg>',
      "sku-3": '<svg width="88" height="88" viewBox="0 0 88 88" fill="none"><rect x="22" y="26" width="40" height="48" rx="5" fill="rgba(255,255,255,.08)" stroke="rgba(255,255,255,.38)" stroke-width="1.5" transform="rotate(-8 42 50)"/><rect x="24" y="24" width="40" height="48" rx="5" fill="rgba(255,255,255,.13)" stroke="rgba(255,255,255,.5)" stroke-width="1.5" transform="rotate(-3 44 48)"/><rect x="26" y="22" width="40" height="48" rx="5" fill="rgba(255,255,255,.2)" stroke="rgba(255,255,255,.8)" stroke-width="1.5"/><line x1="34" y1="36" x2="58" y2="36" stroke="rgba(255,255,255,.6)" stroke-width="1.6" stroke-linecap="round"/><line x1="34" y1="46" x2="58" y2="46" stroke="rgba(255,255,255,.6)" stroke-width="1.6" stroke-linecap="round"/><line x1="34" y1="56" x2="48" y2="56" stroke="rgba(255,255,255,.6)" stroke-width="1.6" stroke-linecap="round"/></svg>'
    };

    /* ─── Helpers ─── */
    function bump(el) {
      el.classList.remove("bump");
      void el.offsetWidth;
      el.classList.add("bump");
      setTimeout(() => el.classList.remove("bump"), 300);
    }

    function setCart(n) {
      cartCount = n;
      [cartCountEl, bagCountEl, bagStatEl].forEach(el => { el.textContent = String(n); });
      bump(cartCountEl);
    }

    function setOrder(n) {
      orderCount = n;
      [orderCountEl, orderStatEl].forEach(el => { el.textContent = String(n); });
      bump(orderCountEl);
    }

    function setStatus(text, ok = true) {
      statusEl.textContent = text;
      statusEl.className   = "activity-box " + (ok ? "ok" : "fail");
    }

    function showTrace(id) {
      const badge   = document.getElementById("traceBadge");
      const content = document.getElementById("traceContent");
      if (!badge || !content) return;
      const jaegerLink = jaegerUrl
        ? '<a class="trace-jaeger" href="' + jaegerUrl + '/trace/' + id +
          '" target="_blank" rel="noreferrer">\u2192 Open in Jaeger</a>'
        : '';
      content.innerHTML = '<code class="trace-id">' + id + '</code>' + jaegerLink;
      badge.style.display = "block";
    }

    function renderProductInfo(payload) {
      const item = payload.item || {};
      const recs = (payload.recommendations || []).map(r => r.id).join(", ") || "none";
      productInfoEl.textContent =
        "sku    " + (item.id   || "n/a") + "\\n" +
        "name   " + (item.name || "n/a") + "\\n" +
        "price  $" + Number(item.price || 0).toFixed(2) + "\\n" +
        "source " + (payload.source || "n/a") + "\\n" +
        "recs   " + recs;
    }

    async function viewProduct(it) {
      try {
        renderProductInfo(await (await fetch("/product/" + it.id)).json());
        setStatus("Viewed " + it.name + ". Product-page trace generated.", true);
      } catch (err) {
        setStatus("Detail load failed: " + err, false);
      }
    }

    function renderItem(it) {
      const meta = productMeta[it.id] || { category: "General", note: "Store item" };
      const grad = artGrad[it.id]     || { v1: "linear-gradient(145deg,#024DA0,#0091DA)", v2: "linear-gradient(145deg,#012060,#024DA0)" };
      const svg  = productSVG[it.id]  || "";
      const bg   = isV2 ? grad.v2 : grad.v1;

      const card = document.createElement("article");
      card.className = "pcard";
      card.innerHTML =
        '<div class="pcard-art" style="background:' + bg + '">' +
          '<span class="pcard-cat">' + meta.category + '</span>' +
          '<span class="pcard-art-svg">' + svg + '</span>' +
        '</div>' +
        '<div class="pcard-body">' +
          '<h3 class="pcard-name">' + it.name + '</h3>' +
          '<p class="pcard-note">' + meta.note + '</p>' +
          '<div class="pcard-footer">' +
            '<span class="pcard-price">$' + Number(it.price).toFixed(2) + '</span>' +
            '<div class="pcard-actions">' +
              '<button class="btn-card details">Details</button>' +
              '<button class="btn-card add-to-bag">+ Bag</button>' +
            '</div>' +
          '</div>' +
        '</div>';

      card.querySelector(".pcard-art").addEventListener("click", () => viewProduct(it));
      card.querySelector(".details").addEventListener("click",   () => viewProduct(it));
      card.querySelector(".add-to-bag").addEventListener("click", () => {
        setCart(cartCount + 1);
        setStatus("Added " + it.name + " to your bag.", true);
      });
      return card;
    }

    async function loadCatalog() {
      try {
        const items = await (await fetch("/catalog")).json();
        itemsEl.innerHTML = "";
        items.forEach(it => itemsEl.appendChild(renderItem(it)));
        setStatus("Collection loaded. Tap a card to view details.", true);
      } catch (err) {
        setStatus("Catalog load failed: " + err, false);
      }
    }

    async function checkout(multiplier) {
      const runs = Number(multiplier || 1);
      let ok = 0;
      let lastTraceId = "";
      try {
        for (let i = 0; i < runs; i++) {
          const resp = await fetch("/checkout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: "order-" + Date.now() + "-" + i, user: "demo-user" })
          });
          if (resp.ok) {
            ok++;
            try {
              const data = await resp.json();
              if (data.trace_id) lastTraceId = data.trace_id;
            } catch (_) {}
          }
          setOrder(orderCount + 1);
        }
        setStatus("Checkout done: " + ok + "/" + runs + " successful.", ok === runs);
        if (lastTraceId) showTrace(lastTraceId);
      } catch (err) {
        setStatus("Checkout failed: " + err, false);
      }
    }

    document.getElementById("refresh").addEventListener("click", loadCatalog);
    document.getElementById("buy").addEventListener("click",     () => checkout(1));
    document.getElementById("bundle").addEventListener("click",  () => checkout(3));
    document.getElementById("addMock").addEventListener("click", () => {
      setCart(cartCount + 3);
      setStatus("Added all products to your bag.", true);
    });

    loadCatalog();
  </script>
</body>
</html>"""
    html = (
        template
        .replace("__TITLE__", title)
        .replace("__SUBTITLE__", subtitle)
        .replace("__BODY_CLASS__", body_class)
        .replace("__STAGE__", stage)
        .replace("__BANNER__", banner)
        .replace("__GOOD_COLOR__", "var(--v2-good)" if is_v2 else "var(--v1-good)")
        .replace("__JAEGER_URL__", jaeger_url)
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
        trace_id = ""
        try:
            from opentelemetry import trace as _ot
            ctx = _ot.get_current_span().get_span_context()
            if ctx and ctx.trace_id:
                trace_id = format(ctx.trace_id, "032x")
        except Exception:
            pass
        return (
            jsonify({
                "items": items,
                "result": resp.json(),
                "frontend_version": frontend_version,
                "trace_id": trace_id,
            }),
            resp.status_code,
            {"X-Frontend-Version": frontend_version},
        )
