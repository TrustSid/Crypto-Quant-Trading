# ETH → LUMIA Lag-Based Trading Bot

A real-time cryptocurrency trading bot that identifies lagged price reactions between ETH and LUMIA. This bot forward-tests a strategy where a sharp pump in ETH triggers a delayed opportunity in LUMIA, exploiting short-term correlation lag.

---

## 🚀 Strategy Logic

> "If ETH rises more than 1.5% in a 1-hour candle, BUY LUMIA 3 hours later, HOLD for 3 hours, then SELL."

* Uses historical correlation data to identify LUMIA as a lagging asset
* Trades are fully fee-adjusted (0.1% per side)
* Portfolio is 100% exposed per trade (no partial risk)
* Compounding returns are tracked

---

## 📁 Repository Structure

```
eth-lumia-lag-trading-bot/
├── bot/
│   └── eth_lumia_bot.py            # Live forward testing engine
├── strategy/
│   └── strategy.py                 # Signal generator (BUY/SELL/HOLD)
├── notebooks/
│   └── anchor_target_analysis.ipynb # Correlation screener for anchor-target pairs
├── logs/
│   └── .gitignore
├── screener/
│   └── lag_screener_6m.py
    └── lag_screener_results.xlsx                
├── LICENSE                         # MIT license
├── README.md                       # This file
├── requirements.txt                # Required Python packages
├── .gitignore                      # Ignored files & folders
```

---

## 📬 Telegram Notifications

The bot sends real-time alerts like:

```
📈 ETH pumped +1.67%. LUMIA buy scheduled at 15:00 UTC
✅ Simulating LUMIA buy at 15:00 for 0.032176
📦 Trade Executed
→ Return: +3.24%
→ PnL: $324.56
💼 Updated Portfolio: $10,324.56
```

---

## 📊 Logs & State

* All trades are saved to: `paper_trade_log_lumia.csv`
* Portfolio state is preserved in: `paper_state_lumia.json`
* These files are excluded from Git via `.gitignore`

---

## 🔧 How to Run the Bot

1. Clone the repository
2. Replace your Telegram token and chat ID in `eth_lumia_bot.py`
3. Run the bot:

```bash
python bot/eth_lumia_bot.py
```

> The bot checks for a new ETH 1H candle every hour. If a signal is detected, it schedules and executes the full trade lifecycle.

---

## 📌 Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

Packages used:

* `pandas`
* `requests`

---

## 📈 Research Summary

This project is based on a 6-month anchor-target screener built in Jupyter. ETH was identified as an anchor with high predictive power on LUMIA using lagged correlation analysis.

Results showed:

* Returns above 90%
* Win rate above 57%
* Sharpe Ratio > 2.8
  

---

## 🙋‍♂️ Author

Built by Krishna Siddharth Suresh as part of a personal exploration into quantitative lag trading strategies. Connect with me on [LinkedIn](https://www.linkedin.com/in/krishna-siddharth-suresh-5150b2112/) or check out more projects on [GitHub](https://github.com/TrustSid).
