# Dividend Low-Vol ETF Live Signals (Streamlit)

A browser tool for **512890 (红利低波 ETF)** based on a 20-day Bollinger Band strategy.  
Enter your account state, then get a Buy / Sell / Hold recommendation in one click.

Data source: [Yahoo Finance](https://finance.yahoo.com/) via `yfinance`.

> **Disclaimer**: For learning and research only. Not investment advice. Past signals do not guarantee future returns; trade at your own risk.

[中文文档](README.md)

## Strategy rules

| Condition | Signal |
|-----------|--------|
| Holding and return ≥ 10% | Sell (close position) |
| Holding and close > 2.0× upper band | Sell (close position) |
| Close < 2.2× lower band and bullets remaining | Buy (add position) |
| Otherwise | Hold / wait (in or out of market) |

Bands are **asymmetric**: the buy threshold uses `2.2×` std below the 20-day MA, while the sell threshold uses `2.0×` std above it. Buys are split into up to 3 equal “bullets” (tranches).

## Run locally

### 1. Install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Start the app

```bash
streamlit run streamlit_app.py
```

The browser should open `http://localhost:8501`.

## Project layout

```
.
├── streamlit_app.py    # Streamlit UI entrypoint
├── strategy.py         # Data fetch + signal logic
├── requirements.txt
├── LICENSE             # MIT
├── README.md           # Chinese
├── README.en.md        # English (this file)
└── .github/workflows/  # Optional Streamlit keep-alive cron
```

## FAQ

**Q: Deployed app shows “data fetch failed”?**  
A: The host must reach Yahoo Finance. If the API rate-limits, retry later.

**Q: Do I need secrets / API keys?**  
A: No. No API key or database is required.

**Q: How do I change strategy parameters?**  
A: Edit `TARGET_PROFIT`, `LOWER_MULT`, and `UPPER_MULT` in `strategy.py`, then redeploy.

## License

[MIT](LICENSE)
