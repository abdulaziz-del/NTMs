from flask import Flask, request, jsonify, send_file
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("WTO_API_KEY", "05b4bc94c24a42af8ffc2710fe9db2e6")
HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Accept": "application/json",
}

ENDPOINTS = {
    "eping":   "https://api.wto.org/eping",
    "itip_ts": "https://api.wto.org/timeseries/v1",
    "ad":      "https://ad-notification.wto.org/api/v2/itip/measures",
    "qr":      "https://qr-notification.wto.org/api/itip/qrs",
    "lic":     "https://lic-notification.wto.org/api/itip/legislations",
    "wits":    "https://wits.worldbank.org/API/V1",
}

def proxy(url, use_key=True):
    try:
        h = HEADERS if use_key else {"Accept": "application/json"}
        r = requests.get(url, headers=h, timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/")
def index():
    # Read index.html from same directory as app.py
    base = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "apis": ["ePing","I-TIP","AD","QR","LIC","WITS"]})

@app.route("/api/eping")
def api_eping():
    t      = request.args.get("type", "sps")
    member = request.args.get("member", "")
    hs     = request.args.get("hs", "")
    size   = request.args.get("pageSize", "20")
    page   = request.args.get("page", "1")
    url = f"{ENDPOINTS['eping']}/v1/epingalertsatoms?type={t}&pageSize={size}&page={page}"
    if member: url += f"&member={member}"
    if hs:     url += f"&hs={hs}"
    return proxy(url)

@app.route("/api/itip/timeseries")
def api_itip():
    ind  = request.args.get("indicator", "ITS_MTV_AX")
    rep  = request.args.get("reportingEconomy", "all")
    yf   = request.args.get("startYear", "2020")
    yt   = request.args.get("endYear", "2024")
    size = request.args.get("pageSize", "100")
    url  = f"{ENDPOINTS['itip_ts']}/data/{ind}?reportingEconomy={rep}&startYear={yf}&endYear={yt}&format=json&pageSize={size}"
    return proxy(url)

@app.route("/api/itip/indicators")
def api_itip_indicators():
    return proxy(f"{ENDPOINTS['itip_ts']}/indicators?format=json")

@app.route("/api/antidumping")
def api_ad():
    size = request.args.get("pageSize", "20")
    page = request.args.get("page", "1")
    rep  = request.args.get("reporter", "")
    url  = f"{ENDPOINTS['ad']}?pageSize={size}&page={page}"
    if rep: url += f"&reportingMember={rep}"
    return proxy(url)

@app.route("/api/qr")
def api_qr():
    size   = request.args.get("pageSize", "20")
    member = request.args.get("member", "")
    hs     = request.args.get("hs", "")
    url    = f"{ENDPOINTS['qr']}?pageSize={size}"
    if member: url += f"&member={member}"
    if hs:     url += f"&hs={hs}"
    return proxy(url)

@app.route("/api/license")
def api_lic():
    size   = request.args.get("pageSize", "20")
    member = request.args.get("member", "")
    year   = request.args.get("year", "")
    url    = f"{ENDPOINTS['lic']}?pageSize={size}"
    if member: url += f"&member={member}"
    if year:   url += f"&year={year}"
    return proxy(url)

@app.route("/api/wits")
def api_wits():
    reporter  = request.args.get("reporter", "SAU")
    partner   = request.args.get("partner", "WLD")
    indicator = request.args.get("indicator", "VI.NTM.ALL.HSALL")
    year      = request.args.get("year", "2023")
    url = f"{ENDPOINTS['wits']}/INDICATOR/{indicator}/{reporter}/{partner}/{year}?format=json"
    return proxy(url, use_key=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
