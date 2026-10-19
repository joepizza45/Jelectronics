(() => {
  const DEAL_TYPE_LABEL = {
    price_error: "Price error",
    flash_sale: "Flash sale",
    clearance: "Clearance",
    major_discount: "Big discount",
  };
  const CHECK_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 4 5v6c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V5zm-1.2 14.2-3.5-3.5 1.4-1.4 2.1 2.1 4.6-4.6 1.4 1.4z"/></svg>';
  const PLACEHOLDER = '<svg class="placeholder" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20M9 16v4M15 16v4"/></svg>';

  const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  const state = { deals: [], featuredId: null, retailer: "All", category: "All", sort: "recommended" };
  const $ = (id) => document.getElementById(id);

  function relativeTime(iso) {
    const mins = Math.round((Date.now() - new Date(iso)) / 60000);
    if (mins < 60) return `${Math.max(mins, 1)} min ago`;
    const hrs = Math.round(mins / 60);
    if (hrs < 48) return `${hrs} hr ago`;
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function safeUrl(url) {
    try {
      const u = new URL(url);
      return u.protocol === "https:" || u.protocol === "http:" ? u.href : "";
    } catch {
      return "";
    }
  }

  function setImage(media, deal) {
    const img = media.querySelector("img");
    const src = safeUrl(deal.image_url);
    img.alt = deal.title;
    const fallback = () => { img.remove(); media.insertAdjacentHTML("afterbegin", PLACEHOLDER); };
    if (!src) return fallback();
    img.addEventListener("error", fallback, { once: true });
    img.src = src;
  }

  function renderCard(deal) {
    const node = $("card-tpl").content.firstElementChild.cloneNode(true);
    const url = safeUrl(deal.url);
    const media = node.querySelector(".card-media");
    media.href = url;
    setImage(media, deal);
    const badge = node.querySelector(".badge");
    badge.textContent = DEAL_TYPE_LABEL[deal.deal_type] || "Deal";
    badge.classList.add(deal.deal_type);

    node.querySelector(".retailer").textContent = deal.retailer;
    node.querySelector(".category").textContent = deal.category;
    node.querySelector(".headline").textContent = deal.headline || deal.title;
    node.querySelector(".headline").title = deal.title;
    node.querySelector(".price").textContent = money.format(deal.price);
    node.querySelector(".was").textContent = money.format(deal.regular_price);
    node.querySelector(".off").textContent = `${deal.discount_pct}% off`;
    node.querySelector(".notes").textContent = deal.notes;

    const verified = node.querySelector(".verified");
    verified.innerHTML = CHECK_ICON;
    verified.append(`Checked ${relativeTime(deal.last_verified)}`);
    verified.title = `Verifier confidence: ${deal.confidence}%`;

    const btn = node.querySelector(".btn");
    btn.href = url;
    btn.textContent = `View at ${deal.retailer}`;
    return node;
  }

  function renderFeatured(deal) {
    const section = $("featured");
    if (!deal) { section.hidden = true; return; }
    const card = renderCard(deal);
    section.replaceChildren(...card.children);
    const label = document.createElement("div");
    label.className = "featured-label";
    label.textContent = "Top deal today";
    section.querySelector(".card-body").prepend(label);
    section.hidden = false;
  }

  function chipRow(container, values, key, allLabel) {
    container.replaceChildren(...["All", ...values].map((value) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = value === "All" ? allLabel : value;
      b.setAttribute("aria-pressed", String(state[key] === value));
      b.addEventListener("click", () => {
        state[key] = value;
        container.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", String(c === b)));
        renderGrid();
      });
      return b;
    }));
  }

  function renderGrid() {
    const sorters = {
      recommended: () => 0,
      discount: (a, b) => b.discount_pct - a.discount_pct,
      savings: (a, b) => (b.regular_price - b.price) - (a.regular_price - a.price),
      price: (a, b) => a.price - b.price,
    };
    const filtered = state.deals
      .filter((d) => d.id !== state.featuredId || state.retailer !== "All" || state.category !== "All")
      .filter((d) => state.retailer === "All" || d.retailer === state.retailer)
      .filter((d) => state.category === "All" || d.category === state.category)
      .sort(sorters[state.sort]);
    $("grid").replaceChildren(...filtered.map(renderCard));
    $("empty").hidden = filtered.length > 0;
  }

  function renderStats(data) {
    const totalSavings = data.deals.reduce((s, d) => s + (d.regular_price - d.price), 0);
    const items = [
      ["Verified deals", data.stats?.verified ?? data.deals.length],
      ["Candidates checked", data.stats?.candidates ?? "–"],
      ["Rejected by verifier", data.stats?.rejected ?? "–"],
      ["Combined savings", money.format(totalSavings).replace(/\.\d\d$/, "")],
    ];
    $("stats").replaceChildren(...items.map(([label, value]) => {
      const div = document.createElement("div");
      const dt = document.createElement("dt");
      const dd = document.createElement("dd");
      dt.textContent = label;
      dd.textContent = value;
      div.append(dt, dd);
      return div;
    }));
  }

  async function init() {
    try {
      const res = await fetch(`data/deals.json?v=${Date.now()}`);
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      state.deals = data.deals || [];
      state.featuredId = data.featured_id;

      const updated = new Date(data.updated_at);
      $("updated").textContent = `Updated ${updated.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}`;
      $("summary").textContent = data.summary;
      $("sample-banner").hidden = !data.sample;
      renderStats(data);
      renderFeatured(state.deals.find((d) => d.id === state.featuredId));

      const uniq = (k) => [...new Set(state.deals.map((d) => d[k]))].sort();
      chipRow($("retailer-filters"), uniq("retailer"), "retailer", "All stores");
      chipRow($("category-filters"), uniq("category"), "category", "All categories");
      $("sort").addEventListener("change", (e) => { state.sort = e.target.value; renderGrid(); });
      renderGrid();
    } catch (err) {
      $("updated").textContent = "Could not load deals";
      $("summary").textContent = "The deals feed is unavailable right now. Please try again later.";
      console.error(err);
    }
  }

  init();
})();
