from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, os, json, logging

app = Flask(__name__, static_folder="static")
CORS(app)
logging.basicConfig(level=logging.INFO)

# ── Keys & Endpoints ──────────────────────────────────────────────────────────
WTO_KEY = os.environ.get("WTO_API_KEY", "05b4bc94c24a42af8ffc2710fe9db2e6")
WTO_H   = {"Ocp-Apim-Subscription-Key": WTO_KEY, "Accept": "application/json"}
WB_H    = {"Accept": "application/json"}

EP = {
    "eping" : "https://api.wto.org/eping/v1",
    "ts"    : "https://api.wto.org/timeseries/v1",
    "ad"    : "https://ad-notification.wto.org/api/v2/itip/measures",
    "qr"    : "https://qr-notification.wto.org/api/itip/qrs",
    "lic"   : "https://lic-notification.wto.org/api/itip/legislations",
    "wits"  : "https://wits.worldbank.org/API/V1",
    "wb"    : "https://api.worldbank.org/v2",
}

def fetch(url, headers=None, timeout=20):
    """Fetch URL and return (data, status_code)."""
    if headers is None:
        headers = WTO_H
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        logging.info(f"GET {url[:80]} → {r.status_code}")
        if r.status_code == 200:
            return r.json(), 200
        return {"error": f"HTTP {r.status_code}", "detail": r.text[:200]}, r.status_code
    except Exception as e:
        logging.error(f"fetch error: {e}")
        return {"error": str(e)}, 502

# ── Static files ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

# ── Health ────────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "4.0",
                    "sources": ["ePing","I-TIP","AD","QR","LIC","WITS","WorldBank"]})

# ═══════════════════════════════════════════════════════════════════════════════
#  ePing — SPS & TBT notifications
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/eping/alerts")
def eping_alerts():
    t    = request.args.get("type", "sps")
    size = request.args.get("pageSize", "20")
    page = request.args.get("page", "1")
    mem  = request.args.get("member", "")
    hs   = request.args.get("hs", "")
    url  = f"{EP['eping']}/epingalertsatoms?type={t}&pageSize={size}&page={page}"
    if mem: url += f"&member={mem}"
    if hs:  url += f"&hs={hs}"
    data, code = fetch(url)
    return jsonify(data), code

@app.route("/api/eping/members")
def eping_members():
    data, code = fetch(f"{EP['eping']}/Members")
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  I-TIP Timeseries
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/itip/data")
def itip_data():
    ind  = request.args.get("indicator", "ITS_MTV_AX")
    rep  = request.args.get("reporter", "all")
    yf   = request.args.get("from", "2021")
    yt   = request.args.get("to", "2023")
    size = request.args.get("pageSize", "100")
    url  = f"{EP['ts']}/data/{ind}?reportingEconomy={rep}&startYear={yf}&endYear={yt}&format=json&pageSize={size}"
    data, code = fetch(url)
    return jsonify(data), code

@app.route("/api/itip/indicators")
def itip_indicators():
    data, code = fetch(f"{EP['ts']}/indicators?format=json")
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  Anti-Dumping
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/ad/measures")
def ad_measures():
    size = request.args.get("pageSize", "20")
    page = request.args.get("page", "1")
    rep  = request.args.get("reporter", "")
    url  = f"{EP['ad']}?pageSize={size}&page={page}"
    if rep: url += f"&reportingMember={rep}"
    data, code = fetch(url)
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  Quantitative Restrictions
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/qr/list")
def qr_list():
    size = request.args.get("pageSize", "20")
    mem  = request.args.get("member", "")
    hs   = request.args.get("hs", "")
    url  = f"{EP['qr']}?pageSize={size}"
    if mem: url += f"&member={mem}"
    if hs:  url += f"&hs={hs}"
    data, code = fetch(url)
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  Import Licensing
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/lic/list")
def lic_list():
    size = request.args.get("pageSize", "20")
    mem  = request.args.get("member", "")
    yr   = request.args.get("year", "")
    url  = f"{EP['lic']}?pageSize={size}"
    if mem: url += f"&member={mem}"
    if yr:  url += f"&year={yr}"
    data, code = fetch(url)
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  WITS World Bank
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/wits/ntm")
def wits_ntm():
    reporter  = request.args.get("reporter", "SAU")
    partner   = request.args.get("partner", "WLD")
    indicator = request.args.get("indicator", "VI.NTM.ALL.HSALL")
    year      = request.args.get("year", "2022")
    url = f"{EP['wits']}/INDICATOR/{indicator}/{reporter}/{partner}/{year}?format=json"
    data, code = fetch(url, headers=WB_H)
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  World Bank Open Data (public, no key needed)
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/worldbank/trade")
def wb_trade():
    country   = request.args.get("country", "SAU")
    indicator = request.args.get("indicator", "TM.TAX.MRCH.SM.AR.ZS")
    url = f"{EP['wb']}/indicator/{indicator}?country={country}&format=json&per_page=10&mrv=5"
    data, code = fetch(url, headers=WB_H)
    return jsonify(data), code

@app.route("/api/worldbank/countries")
def wb_countries():
    url = f"{EP['wb']}/country?format=json&per_page=300"
    data, code = fetch(url, headers=WB_H)
    return jsonify(data), code

# ═══════════════════════════════════════════════════════════════════════════════
#  Aggregate endpoint — Dashboard data (all sources in one call)
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/dashboard")
def dashboard():
    results = {}

    # ePing SPS
    d, c = fetch(f"{EP['eping']}/epingalertsatoms?type=sps&pageSize=10")
    results["sps"] = {"data": d, "status": c, "source": "ePing WTO"}

    # ePing TBT
    d, c = fetch(f"{EP['eping']}/epingalertsatoms?type=tbt&pageSize=10")
    results["tbt"] = {"data": d, "status": c, "source": "ePing WTO"}

    # Anti-Dumping
    d, c = fetch(f"{EP['ad']}?pageSize=10")
    results["ad"] = {"data": d, "status": c, "source": "WTO AD Notifications"}

    # QR
    d, c = fetch(f"{EP['qr']}?pageSize=10")
    results["qr"] = {"data": d, "status": c, "source": "WTO QR Notifications"}

    # Import License
    d, c = fetch(f"{EP['lic']}?pageSize=10")
    results["lic"] = {"data": d, "status": c, "source": "WTO Import License"}

    # World Bank trade (public)
    d, c = fetch(f"{EP['wb']}/indicator/TM.TAX.MRCH.SM.AR.ZS?country=SAU&format=json&per_page=5&mrv=3", headers=WB_H)
    results["wb_tariff"] = {"data": d, "status": c, "source": "World Bank Open Data"}

    return jsonify(results)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
