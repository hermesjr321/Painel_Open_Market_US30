from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

# ============================
# TICKERS
# ============================
TICKERS = {
    "US30": "^DJI",
    "YM_FUT": "YM=F",
    "US500": "^GSPC",
    "US100": "^IXIC",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB"
}

TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "60m",
    "4h": "240m",
    "1d": "1d"
}

# ============================
# FUNÇÕES PRINCIPAIS
# ============================

def get_multitimeframe(ticker):
    out = {}
    for name, tf in TIMEFRAMES.items():
        try:
            df = yf.download(ticker, period="5d", interval=tf, progress=False)
            if df.empty:
                out[name] = None
                continue
            price = float(df["Close"].iloc[-1])
            var = ((df["Close"].iloc[-1] - df["Close"].iloc[-2]) /
                   df["Close"].iloc[-2]) * 100 if len(df) > 2 else 0
            out[name] = {"price": round(price, 2), "var": round(var, 2)}
        except:
            out[name] = None
    return out


def get_gap(ticker):
    df = yf.download(ticker, period="5d", interval="1d", progress=False)
    if len(df) < 2:
        return 0
    gap = (df["Open"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]
    return round(gap * 100, 2)


def get_volume_status(ticker):
    df = yf.download(ticker, period="5d", interval="30m", progress=False)
    if df.empty:
        return 0, 0, 0

    df.index = pd.to_datetime(df.index)
    daily_vol = df.groupby(df.index.date)["Volume"].sum()

    current_vol = int(daily_vol.iloc[-1])
    avg_vol = int(daily_vol.mean())

    ratio = round(current_vol / avg_vol, 2) if avg_vol > 0 else 0
    return current_vol, avg_vol, ratio


def dow_breadth():
    dow30 = [
        "MMM","AXP","AMGN","AAPL","BA","CAT","CVX","CSCO","KO","DOW","GS",
        "HD","HON","IBM","INTC","JNJ","JPM","MCD","MRK","MSFT","NKE","PG",
        "CRM","TRV","UNH","VZ","V","AMZN","WMT","DIS"
    ]

    pos, neg = 0, 0
    details = {}

    for stock in dow30:
        df = yf.download(stock, period="1d", interval="1d", progress=False)
        if df.empty:
            continue
        var = ((df["Close"].iloc[-1] - df["Open"].iloc[-1]) /
               df["Open"].iloc[-1]) * 100

        if var > 0:
            pos += 1
            details[stock] = ("🟢", round(var, 2))
        else:
            neg += 1
            details[stock] = ("🔴", round(var, 2))

    return pos, neg, details


def volume_profile_poc():
    df = yf.download("^DJI", period="1d", interval="15m", progress=False)
    if df.empty:
        return 0, 0

    df["price"] = ((df["High"] + df["Low"]) / 2).round(0)
    prof = df.groupby("price")["Volume"].sum()

    poc_price = int(prof.idxmax())
    poc_vol = int(prof.max())

    return poc_price, poc_vol


def overnight_structure():
    df = yf.download("YM=F", period="1d", interval="30m", progress=False)
    if df.empty:
        return None

    high = float(df["High"].max())
    low = float(df["Low"].min())
    mid = (high + low) / 2
    last = float(df["Close"].iloc[-1])

    range_total = high - low
    pos = ((last - low) / range_total) * 100 if range_total > 0 else 0

    return {
        "high": round(high, 2),
        "low": round(low, 2),
        "mid": round(mid, 2),
        "range": round(range_total, 2),
        "price": round(last, 2),
        "position": round(pos, 2)
    }


# ============================
# ROUTE PRINCIPAL
# ============================

@app.route("/")
def dashboard():
    prices = {k: get_multitimeframe(v) for k, v in TICKERS.items()}

    gaps = {
        "US30": get_gap("^DJI"),
        "YM_FUT": get_gap("YM=F")
    }

    vol_now, vol_avg, vol_ratio = get_volume_status("^DJI")

    pos, neg, dow_details = dow_breadth()

    poc_price, poc_vol = volume_profile_poc()

    overnight = overnight_structure()

    return render_template(
        "index.html",
        prices=prices,
        gaps=gaps,
        vol_now=vol_now,
        vol_avg=vol_avg,
        vol_ratio=vol_ratio,
        pos=pos,
        neg=neg,
        dow_details=dow_details,
        poc_price=poc_price,
        poc_vol=poc_vol,
        overnight=overnight
    )


if __name__ == "__main__":
    app.run(debug=True)

