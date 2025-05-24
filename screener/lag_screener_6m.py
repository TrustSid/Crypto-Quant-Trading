import requests
import pandas as pd
import time
from datetime import datetime, timedelta

BASE_URL = "https://api.binance.com/api/v3/klines"

# --- CONFIG ---
ANCHORS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
INTERVAL = '1h'
DAYS_BACK = 180
LAG_RANGE = 12
MIN_VOLUME_USD = 5_000_000

# --- UTILS ---
def interval_to_minutes(interval):
    if interval.endswith('m'):
        return int(interval[:-1])
    elif interval.endswith('h'):
        return int(interval[:-1]) * 60
    elif interval.endswith('d'):
        return int(interval[:-1]) * 1440
    return 60

def fetch_ohlcv(symbol, interval, start_time, end_time):
    url = BASE_URL
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': int(start_time.timestamp() * 1000),
        'endTime': int(end_time.timestamp() * 1000),
        'limit': 1000
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]

def get_symbol_list():
    info = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()
    symbols = [s['symbol'] for s in info['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return sorted(list(set(symbols)))

def get_avg_volume_usdt(symbol):
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url, params={'symbol': symbol}).json()
    try:
        return float(data['quoteVolume'])
    except:
        return 0

def download_history(symbol):
    print(f"\n📥 Downloading {symbol}...")
    now = datetime.utcnow()
    start = now - timedelta(days=DAYS_BACK)
    all_data = []
    while start < now:
        end = start + timedelta(minutes=interval_to_minutes(INTERVAL) * 1000)
        df = fetch_ohlcv(symbol, INTERVAL, start, end)
        if df.empty:
            break
        all_data.append(df)
        start = df['timestamp'].iloc[-1] + timedelta(minutes=interval_to_minutes(INTERVAL))
        time.sleep(0.3)
    full_df = pd.concat(all_data)
    full_df.drop_duplicates(subset='timestamp', inplace=True)
    return full_df

def run_lag_correlation(anchor_df, target_df):
    merged = pd.merge(anchor_df, target_df, on='timestamp', suffixes=('_anchor', '_target'))
    merged['ret_anchor'] = merged['close_anchor'].pct_change()
    merged['ret_target'] = merged['close_target'].pct_change()
    best_corr = 0
    best_lag = None
    for lag in range(1, LAG_RANGE + 1):
        merged[f'ret_target_lag{lag}'] = merged['ret_target'].shift(-lag)
        corr = merged[['ret_anchor', f'ret_target_lag{lag}']].corr().iloc[0, 1]
        if pd.notna(corr) and abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    return best_lag, best_corr

def main():
    symbols = get_symbol_list()
    results = []
    for anchor in ANCHORS:
        anchor_df = download_history(anchor)
        for target in symbols:
            if target == anchor:
                continue
            vol = get_avg_volume_usdt(target)
            if vol < MIN_VOLUME_USD:
                continue
            try:
                target_df = download_history(target)
                lag, corr = run_lag_correlation(anchor_df, target_df)
                if abs(corr) >= 0.03:
                    results.append({
                        'anchor': anchor,
                        'target': target,
                        'lag_hr': lag,
                        'correlation': round(corr, 5),
                        'avg_volume_usdt': round(vol, 2)
                    })
            except Exception as e:
                print(f"⚠️ Skipping {target} due to error: {e}")

    df_results = pd.DataFrame(results)
    df_results.sort_values(by='correlation', ascending=False, key=abs, inplace=True)
    df_results.to_excel("lag_screener_results.xlsx", index=False)
    print("\n✅ Screener complete. Top results saved to 'lag_screener_results.xlsx'.")

if __name__ == "__main__":
    main()
