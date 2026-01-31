from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import time

app = Flask(__name__)

# =========================
# TICKERS
# =========================
US30   = "^DJI"
YM_FUT = "YM=F"
US500  = "^GSPC"
US100  = "^IXIC"
VIX    = "^VIX"
DXY    = "DX-Y.NYB"

TIMEFRAMES = ["1m","5m","15m","30m","1h","4h","1d"]

# =========================
# CACHE CONFIG
# =========================
CACHE = {}
CACHE_TIME = 300  # 5 minutos

# =========================
# FUNÇÃO MULTI-TF
# =========================
def fetch_multitf(ticker):
    out = {}
    for tf in TIMEFRAMES:
        try:
            df = yf.download(ticker, period="5d", interval=tf, progress=False)
            if df.empty:
                out[tf] = None
            else:
                price = float(df["Close"].iloc[-1])
                out[tf] = round(price, 2)
        except:
            out[tf] = None
    return out

# =========================
# GAP DO DIA
# =========================
def calc_gap(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        open_today = df.iloc[-1]["Open"]
        close_yest = df.iloc[-2]["Close"]
        return round(((open_today - close_yest) / close_yest) * 100, 3)
    except:
        return 0.0

# =========================
# VOLUME + MÉDIA
# =========================
def volume_status():
    try:
        df = yf.download(US30, period="1d", interval="30m", progress=False)
        current_vol = int(df["Volume"].sum())

        df5 = yf.download(US30, period="5d", interval="30m", progress=False)
        df5.index = pd.to_datetime(df5.index)
        daily = df5.groupby(df5.index.date)["Volume"].sum()
        avg_vol = int(daily.mean())

        ratio = round(current_vol / avg_vol, 2) if avg_vol > 0 else 0

        return current_vol, avg_vol, ratio
    except:
        return 0, 0, 0

# =========================
# VOLUME PROFILE POC
# =========================
def volume_profile_poc():
    try:
        df = yf.download(US30, period="1d", interval="15m", progress=False).dropna()
        df["price"] = ((df["High"] + df["Low"]) / 2).round(0)

        prof = df.groupby("price")["Volume"].sum()
        poc_price = int(prof.idxmax())
        poc_vol = int(prof.max())

        current_price = float(df["Close"].iloc[-1])

        return poc_price, poc_vol, round(current_price, 2)
    except:
        return 0, 0, 0

# =========================
# OVERNIGHT STRUCTURE YM
# =========================
def overnight_structure():
    try:
        df = yf.download(YM_FUT, period="1d", interval="30m", progress=False)

        overnight = df.between_time("00:00", "09:29")

        high = float(overnight["High"].max())
        low  = float(overnight["Low"].min())
        mid  = round((high + low) / 2, 2)

        current = float(df["Close"].iloc[-1])
        rng = round(high - low, 2)

        pos = round(((current - low) / rng) * 100, 2) if rng > 0 else 0

        return {
            "high": round(high, 2),
            "low": round(low, 2),
            "mid": mid,
            "range": rng,
            "current": round(current, 2),
            "position": pos
        }
    except:
        return {}

# =========================
# LOAD ALL DATA
# =========================
def load_all_data():

    assets = {
        "US30": fetch_multitf(US30),
        "YM FUT": fetch_multitf(YM_FUT),
        "US500": fetch_multitf(US500),
        "US100": fetch_multitf(US100),
        "VIX": fetch_multitf(VIX),
        "DXY": fetch_multitf(DXY)
    }

    gaps = {
        "US30 Gap %": calc_gap(US30),
        "YM Gap %": calc_gap(YM_FUT)
    }

    vol_now, vol_avg, vol_ratio = volume_status()

    poc_price, poc_vol, current_price = volume_profile_poc()

    overnight = overnight_structure()

    return {
        "assets": assets,
        "gaps": gaps,
        "volume": {
            "now": vol_now,
            "avg": vol_avg,
            "ratio": vol_ratio
        },
        "poc": {
            "price": poc_price,
            "volume": poc_vol,
            "current": current_price
        },
        "overnight": overnight
    }

# =========================
# ROUTE PRINCIPAL
# =========================
@app.route("/")
def index():

    now = time.time()

    if "data" not in CACHE or now - CACHE["time"] > CACHE_TIME:
        print("🔄 Atualizando dados...")
        CACHE["data"] = load_all_data()
        CACHE["time"] = now

    data = CACHE["data"]

    return render_template(
        "index.html",
        assets=data["assets"],
        gaps=data["gaps"],
        volume=data["volume"],
        poc=data["poc"],
        overnight=data["overnight"]
    )

# =========================
# START SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
