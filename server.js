const express = require("express");
const fetch = require("node-fetch");
const cors = require("cors");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;

// ── API Keys ─────────────────────────────────────────────────────────────────
const API_KEY = process.env.WTO_API_KEY || "05b4bc94c24a42af8ffc2710fe9db2e6";

// ── Middleware ────────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// ── Shared fetch helper ───────────────────────────────────────────────────────
async function proxyFetch(res, url) {
  try {
    const r = await fetch(url, {
      headers: {
        "Ocp-Apim-Subscription-Key": API_KEY,
        "Accept": "application/json",
      },
    });
    const ct = r.headers.get("content-type") || "";
    if (!r.ok) {
      const text = await r.text();
      return res.status(r.status).json({ error: `Upstream ${r.status}`, detail: text });
    }
    if (ct.includes("application/json")) {
      const data = await r.json();
      return res.json(data);
    }
    const text = await r.text();
    return res.send(text);
  } catch (err) {
    console.error("proxyFetch error:", err.message);
    return res.status(502).json({ error: "Bad Gateway", detail: err.message });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PROXY ROUTES
// ═══════════════════════════════════════════════════════════════════════════════

// ── 1. ePing ──────────────────────────────────────────────────────────────────
app.get("/api/eping", async (req, res) => {
  const { type = "sps", member = "", hs = "", pageSize = 20, page = 1 } = req.query;
  let url = `https://api.wto.org/eping/v1/epingalertsatoms?type=${type}&pageSize=${pageSize}&page=${page}`;
  if (member) url += `&member=${member}`;
  if (hs)     url += `&hs=${hs}`;
  await proxyFetch(res, url);
});

// ── 2. I-TIP Timeseries ───────────────────────────────────────────────────────
app.get("/api/itip/timeseries", async (req, res) => {
  const {
    indicator = "ITS_MTV_AX",
    reportingEconomy = "all",
    partnerEconomy = "",
    startYear = "2020",
    endYear = "2024",
    format = "json",
    pageSize = 100,
  } = req.query;
  let url = `https://api.wto.org/timeseries/v1/data/${indicator}?reportingEconomy=${reportingEconomy}&startYear=${startYear}&endYear=${endYear}&format=${format}&pageSize=${pageSize}`;
  if (partnerEconomy) url += `&partnerEconomy=${partnerEconomy}`;
  await proxyFetch(res, url);
});

// ── 3. Anti-Dumping ───────────────────────────────────────────────────────────
app.get("/api/antidumping", async (req, res) => {
  const { pageSize = 20, page = 1, reporter = "", product = "" } = req.query;
  let url = `https://ad-notification.wto.org/api/v2/itip/measures?pageSize=${pageSize}&page=${page}`;
  if (reporter) url += `&reportingMember=${reporter}`;
  if (product)  url += `&product=${encodeURIComponent(product)}`;
  await proxyFetch(res, url);
});

// ── 4. Quantitative Restrictions ─────────────────────────────────────────────
app.get("/api/qr", async (req, res) => {
  const { pageSize = 20, page = 1, member = "", hs = "", type = "" } = req.query;
  let url = `https://qr-notification.wto.org/api/itip/qrs?pageSize=${pageSize}&page=${page}`;
  if (member) url += `&member=${member}`;
  if (hs)     url += `&hs=${hs}`;
  if (type)   url += `&type=${type}`;
  await proxyFetch(res, url);
});

// ── 5. Import Licensing ───────────────────────────────────────────────────────
app.get("/api/license", async (req, res) => {
  const { pageSize = 20, page = 1, member = "", year = "" } = req.query;
  let url = `https://lic-notification.wto.org/api/itip/legislations?pageSize=${pageSize}&page=${page}`;
  if (member) url += `&member=${member}`;
  if (year)   url += `&year=${year}`;
  await proxyFetch(res, url);
});

// ── 6. WITS World Bank ────────────────────────────────────────────────────────
app.get("/api/wits", async (req, res) => {
  const { reporter = "SAU", partner = "WLD", indicator = "VI.NTM.ALL.HSALL", year = "2023" } = req.query;
  const url = `https://wits.worldbank.org/API/V1/INDICATOR/${indicator}/${reporter}/${partner}/${year}?format=json`;
  // WITS does not require the WTO key
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if (!r.ok) {
      const t = await r.text();
      return res.status(r.status).json({ error: `WITS ${r.status}`, detail: t });
    }
    const data = await r.json();
    return res.json(data);
  } catch (err) {
    return res.status(502).json({ error: "WITS proxy error", detail: err.message });
  }
});

// ── 7. WTO Timeseries Indicators list ────────────────────────────────────────
app.get("/api/itip/indicators", async (req, res) => {
  await proxyFetch(res, "https://api.wto.org/timeseries/v1/indicators?format=json");
});

// ── 8. Health check ───────────────────────────────────────────────────────────
app.get("/api/health", (_req, res) => {
  res.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    apis: ["ePing", "I-TIP Timeseries", "Anti-Dumping", "QR", "Import License", "WITS"],
  });
});

// ── SPA fallback ──────────────────────────────────────────────────────────────
app.get("*", (_req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// ── Start ─────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`✅ NTM Watch server running on port ${PORT}`);
  console.log(`   → http://localhost:${PORT}`);
});
