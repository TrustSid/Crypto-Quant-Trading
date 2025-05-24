import pandas as pd

def generate_signals(candles_target: pd.DataFrame, candles_anchor: pd.DataFrame) -> pd.DataFrame:
    """
    Strategy:
    - Detect if ETH pumped ≥1.5% between the last two closed 1H candles (i-2 to i-1).
    - If yes, schedule a BUY for LUMIA at i+3 and SELL at i+6 (3-hour hold).

    Inputs:
    - candles_target: OHLCV for LUMIA (1H)
    - candles_anchor: OHLCV with 'close_ETH_1H' (ETH 1H close prices)

    Output:
    - DataFrame with ['timestamp', 'signal']
    """
    try:
        df = candles_target[['timestamp']].copy()

        # Merge ETH 1H close prices
        df = pd.merge(
            df,
            candles_anchor[['timestamp', 'close_ETH_1H']],
            on='timestamp',
            how='inner'
        )

        n = len(df)
        signals = ['HOLD'] * n  # Default all to HOLD

        # Loop safely until n - 6 to avoid overflow (SELL at i+6)
        for i in range(2, n - 6):
            prev_close = df['close_ETH_1H'].iloc[i - 2]
            curr_close = df['close_ETH_1H'].iloc[i - 1]

            if prev_close > 0:
                pump_pct = ((curr_close - prev_close) / prev_close) * 100

                if pump_pct >= 1.5:
                    signals[i + 3] = 'BUY'
                    signals[i + 6] = 'SELL'

        df['signal'] = signals
        return df[['timestamp', 'signal']]

    except Exception as e:
        raise RuntimeError(f"Error in generate_signals: {e}")


def get_coin_metadata() -> dict:
    """
    Specifies the target and anchor coins used in this strategy.
    """
    return {
        "target": {
            "symbol": "LUMIA",
            "timeframe": "1H"
        },
        "anchors": [
            {"symbol": "ETH", "timeframe": "1H"}
        ]
    }
