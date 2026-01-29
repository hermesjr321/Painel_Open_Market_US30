from flask import Flask, render_template
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

DOW30_COMPONENTS = [
    "MMM","AXP","AMGN","AAPL","BA","CAT","CVX","CSCO","KO","DOW","GS",
    "HD","HON","IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE","PG",
    "CRM","TRV","UNH","VZ","V","AMZN","WMT","DIS"
]

# =========================
# TIMEFRAMES
# =========================
TIMEFRAMES = ["1m","5m","15m","30m","1h","4h","1d"]

PERIOD_MAP = {
    "1m":"1d",
    "5m":"1d",
    "15m":"5d",
    "30m":"5d",
    "1h":"5d",
    "4h":"1mo",
    "1d":"3mo"
}

# =========================
# MULTI-TF DATA
# =========================
def fetch_multitf(ticker):
    data = {}

    for tf in TIMEFRAMES:
        try:
            df = yf.download(
                ticker,
                period=PERIOD_MAP[tf],
                interval=tf,
                progress=False,
                auto_adjust=True
            )

            price = float(df["Close"].iloc[-1])
            change = ((df["Close"].iloc[-1] - df["Close"].iloc[-2])
                      / df["Close"].iloc[-2]) * 100

            volume = float(df["Volume"].iloc[-1]) if "Volume" in df else 0
            avg_vol = float(df["Volume"].mean()) if "Volume" in df else 0

            data[tf] = {
                "price": round(price,2),
                "change": round(change,2),
                "volume": int(volume),
                "avg_volume": int(avg_vol),
                "vol_ratio": round(volume/avg_vol,2) if avg_vol>0 else 0
            }

        except:
            data[tf] = {"price":0,"change":0,"volume":0,"avg_volume":0,"vol_ratio":0}

    return data

# =========================
# GAP DO DIA (%)
# =========================
def calc_gap(ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1d", auto_adjust=True, progress=False)
        today_open = df.iloc[-1]["Open"]
        prev_close = df.iloc[-2]["Close"]
        gap = ((today_open - prev_close) / prev_close) * 100
        return round(gap,2)
    except:
        return 0

# =========================
# BREADTH DOW30 (20x10)
# =========================
def dow_breadth():
    pos = 0
    neg = 0

    for stock in DOW30_COMPONENTS:
        try:
            df = yf.download(stock, period="2d", interval="1d", auto_adjust=True, progress=False)
            var = (df["Close"].iloc[-1] - df["Open"].iloc[-1]) / df["Open"].iloc[-1]

            if var > 0:
                pos += 1
            else:
                neg += 1
        except:
            pass

    return pos, neg

# =========================
# VOLUME PROFILE POC (APROX)
# =========================
def volume_profile_poc():
    try:
        df = yf.download(US30, period="1d", interval="15m", auto_adjust=True, progress=False)

        df["price"] = ((df["High"] + df["Low"]) / 2).round(0)
        profile = df.groupby("price")["Volume"].sum()

        poc_price = int(profile.idxmax())
        current_price = float(df["Close"].iloc[-1])

        return poc_price, round(current_price,2)

    except:
        return 0, 0

# =========================
# OVERNIGHT STRUCTURE YM
# =========================
def overnight_structure():
    try:
        df = yf.download(YM_FUT, period="1d", interval="30m", auto_adjust=True, progress=False)

        high = float(df["High"].max())
        low = float(df["Low"].min())
        mid = (high + low) / 2
        current = float(df["Close"].iloc[-1])

        rng = high - low
        pos = ((current - low) / rng) * 100 if rng > 0 else 0

        return {
            "high": round(high,2),
            "low": round(low,2),
            "mid": round(mid,2),
            "range": round(rng,2),
            "current": round(current,2),
            "position": round(pos,2)
        }

    except:
        return {}

# =========================
# ROUTE
# =========================
@app.route("/")
def index():

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

    breadth = dow_breadth()

    poc_price, current_price = volume_profile_poc()

    overnight = overnight_structure()

    return render_template(
        "index.html",
        assets=assets,
        gaps=gaps,
        breadth=breadth,
        poc=poc_price,
        current=current_price,
        overnight=overnight
    )


if __name__ == "__main__":
    app.run(debug=True)
