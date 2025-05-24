import requests
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import os

# --- PARAMETERS ---
ETH_THRESHOLD = 0.015
LAG_HOURS = 3
HOLD_HOURS = 3

PORTFOLIO_START = 10000

STATE_FILE = "paper_state_lumia.json"
LOG_FILE = "paper_trade_log_lumia.csv"

# --- TELEGRAM CONFIG ---
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# --- SEND TELEGRAM ALERT ---
def send_telegram(msg):
    print(f"\n💬 Telegram Message: {msg}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"⚠️ Telegram API Error: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

# --- DATA FETCHING ---
def fetch_ohlcv(symbol, interval='1h', limit=60):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'num_trades', 'tb_base', 'tb_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

def get_merged_data():
    eth = fetch_ohlcv("ETHUSDT")
    lumia = fetch_ohlcv("LUMIAUSDT")
    eth.columns = ['timestamp'] + [f"{col}_eth" for col in eth.columns[1:]]
    lumia.columns = ['timestamp'] + [f"{col}_lumia" for col in lumia.columns[1:]]
    df = pd.merge(eth, lumia, on='timestamp')
    df['eth_ret'] = df['close_eth'].pct_change()
    return df

# --- STATE MANAGEMENT ---
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
            if state.get('last_run'):
                state['last_run'] = datetime.fromisoformat(state['last_run'])
            for trade in state.get('open_trades', []):
                if trade.get('buy_time'):
                    trade['buy_time'] = datetime.fromisoformat(trade['buy_time'])
            return state
    return {"portfolio": PORTFOLIO_START, "open_trades": [], "last_run": None}

def save_state(state):
    state_to_save = state.copy()
    if state_to_save.get('last_run'):
        state_to_save['last_run'] = state_to_save['last_run'].isoformat()
    for trade in state_to_save.get('open_trades', []):
        if trade.get('buy_time'):
            trade['buy_time'] = trade['buy_time'].isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state_to_save, f, indent=2)

# --- TRADE LOGGING ---
def log_trade(trade):
    df = pd.DataFrame([trade])
    try:
        df.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)
    except Exception as e:
        print(f"⚠️ Failed to log trade: {e}")

# --- TRADE SIMULATION ---
def simulate_trade(entry_price, trade_window, state):
    FEE = 0.001  # 0.1% fee per side
    if trade_window.empty:
        exit_price = entry_price
    else:
        exit_price = trade_window['close_lumia'].iloc[-1]
    entry_price_adj = entry_price * (1 + FEE)
    exit_price_adj = exit_price * (1 - FEE)
    ret = (exit_price_adj - entry_price_adj) / entry_price_adj
    pnl = state['portfolio'] * ret
    state['portfolio'] += pnl
    return exit_price, ret, pnl

# --- MAIN EXECUTION CYCLE ---
def run_cycle():
    merged = get_merged_data()
    state = load_state()

    if len(merged) < 2:
        send_telegram("⚠️ Not enough data to run.")
        save_state(state)
        return

    latest_ts = merged['timestamp'].iloc[-2]
    latest_ret = merged['eth_ret'].iloc[-2]
    send_telegram(f"[{latest_ts}] ETH return = {latest_ret:.2%}")

    scheduled_buy_time = latest_ts + timedelta(hours=LAG_HOURS)
    already_processed = any(
        t['buy_time'] == scheduled_buy_time and t['status'] == 'scheduled'
        for t in state['open_trades']
    )

    if latest_ret > ETH_THRESHOLD and not already_processed:
        state['open_trades'].append({"buy_time": scheduled_buy_time, "status": "scheduled"})
        send_telegram(f"📈 ETH pumped {latest_ret:.2%}. LUMIA buy scheduled at {scheduled_buy_time}")
    elif not already_processed:
        send_telegram(f"[{latest_ts}] No signal detected.")

    updated_trades = []
    for trade in state['open_trades']:
        buy_time = trade['buy_time']
        if trade['status'] == 'scheduled' and buy_time <= latest_ts:
            entry_row = merged[merged['timestamp'] == buy_time]
            if entry_row.empty:
                send_telegram(f"⚠️ No data for buy time: {buy_time}")
                continue
            entry_price = entry_row['close_lumia'].iloc[0]
            send_telegram(f"✅ Simulating LUMIA buy at {buy_time} for {entry_price:.6f}")
            send_telegram(f"⏳ Hold period = {HOLD_HOURS}h.")
            exit_time = buy_time + timedelta(hours=HOLD_HOURS)
            trade_window = merged[(merged['timestamp'] > buy_time) & (merged['timestamp'] <= min(exit_time, latest_ts))]
            exit_price, ret, pnl = simulate_trade(entry_price, trade_window, state)
            if exit_time <= latest_ts:
                trade_log = {
                    "entry_time": str(buy_time),
                    "exit_time": str(min(exit_time, latest_ts)),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "return_pct": round(ret, 5),
                    "pnl": round(pnl, 2),
                    "portfolio_after": round(state['portfolio'], 2)
                }
                log_trade(trade_log)
                send_telegram(
                    f"📦 Trade Executed\n"
                    f"→ Return: {ret:.2%}\n"
                    f"→ PnL: ${pnl:.2f}\n"
                    f"💼 Updated Portfolio: ${state['portfolio']:.2f}"
                )
            else:
                updated_trades.append(trade)
        else:
            updated_trades.append(trade)

    state["open_trades"] = updated_trades
    state["last_run"] = latest_ts
    save_state(state)

# === ENTRY POINT ===
if __name__ == "__main__":
    print("🚀 ETH → LUMIA Live Forward Simulation Started")
    send_telegram("🚀 ETH → LUMIA Live Forward Simulation Started")
    while True:
        try:
            run_cycle()
        except Exception as e:
            err = f"❌ Error occurred: {e}"
            print(err)
            send_telegram(err)
        time.sleep(3600)
