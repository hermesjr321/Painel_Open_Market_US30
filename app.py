from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

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

# =========================
# MULTI TIMEFRAME PRICE
# =========================
def fetch_multitf(ticker):
    tfs = {
        "1m": "1d",
        "5m": "1d",
        "15m": "1d",
        "30m": "5d",
        "1h": "5d",
        "4h": "1mo",
        "1d": "6mo"
    }

    data = {}
    for tf, period in tfs.items():
        try:
            df = yf.download(ticker, period=period, interval=tf, progress=False)
            if df.empty:
                data[tf] = None
            else:
                price = float(df["Close"].iloc[-1])
                change = float((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100)
                data[tf] = {"price": round(price, 2), "pct": round(change, 2)}
        except:
            data[tf] = None

    return data

# =========================
# GAP %
# =========================
def calc_gap(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        o = float(df.iloc[-1]["Open"])
        c = float(df.iloc[-2]["Close"])
        return round(((o - c) / c) * 100, 2)
    except:
        return 0.0

# =========================
# DOW30 BREADTH
# =========================
dow_components = [
    "MMM","AXP","AMGN","AAPL","BA","CAT","CVX","CSCO","KO","DOW","GS",
    "HD","HON","IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE","PG",
    "CRM","TRV","UNH","VZ","V","AMZN","WMT","DIS"
]

def dow_breadth():
    pos = 0
    neg = 0
    for t in dow_components:
        try:
            df = yf.download(t, period="2d", interval="1d", progress=False)
            var = float((df["Close"].iloc[-1] - df["Open"].iloc[-1]) / df["Open"].iloc[-1] * 100)
            if var > 0:
                pos += 1
            else:
                neg += 1
        except:
            pass
    return {"positive": pos, "negative": neg}

# =========================
# VOLUME PROFILE POC
# =========================
def volume_profile_poc():
    try:
        df = yf.download(US30, period="1d", interval="15m", progress=False).dropna()
        df["price"] = ((df["High"] + df["Low"]) / 2).round(0)
        prof = df.groupby("price")["Volume"].sum()
        poc = int(prof.idxmax())
        current = float(df["Close"].iloc[-1])
        return poc, round(current, 2)
    except:
        return 0, 0

# =========================
# OVERNIGHT STRUCTURE YM
# =========================
def overnight_structure():
    try:
        df = yf.download(YM_FUT, period="1d", interval="30m", progress=False)
        high = float(df["High"].max())
        low = float(df["Low"].min())
        mid = (high + low) / 2
        current = float(df["Close"].iloc[-1])
        rng = high - low
        pos = ((current - low) / rng) * 100 if rng != 0 else 0

        return {
            "high": round(high, 2),
            "low": round(low, 2),
            "mid": round(mid, 2),
            "range": round(rng, 2),
            "current": round(current, 2),
            "position": round(pos, 1)
        }
    except:
        return {}

# =========================
# ROUTE
# =========================
@app.route("/", methods=["GET", "HEAD"])
def index():

    if request.method == "HEAD":
        return "", 200

    assets = {
        "US30": fetch_multitf(US30),
        "YM FUT": fetch_multitf(YM_FUT),
        "US500": fetch_multitf(US500),
        "US100": fetch_multitf(US100),
        "VIX": fetch_multitf(VIX),
        "DXY": fetch_multitf(DXY)
    }

    gaps = {
        "US30 Index Gap %": calc_gap(US30),
        "YM Futures Gap %": calc_gap(YM_FUT)
    }

    breadth = dow_breadth()
    poc, current = volume_profile_poc()
    overnight = overnight_structure()

    return render_template(
        "index.html",
        assets=assets,
        gaps=gaps,
        breadth=breadth,
        poc=poc,
        current=current,
        overnight=overnight
    )

# =========================
# RUN LOCAL
# =========================
if __name__ == "__main__":
    app.run()
