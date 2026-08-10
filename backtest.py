"""Backtest Bollinger signals with 512890 <-> 银华日利 (511880) rotation.

Assumptions:
- Signal from day's close; fills at the next trading day's open.
- Up to 3 buy "bullets", each BULLET_SIZE RMB, round down to 100-share lots.
- After a full exit, bullets reset to 3.
- Uninvested capital always sits in 银华日利 and earns its cumulative-NAV daily return
  (AkShare 累计净值; Yahoo trade prices alone understate MMF yield).
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import akshare as ak
import numpy as np
import pandas as pd
import yfinance as yf

from strategy import LOWER_MULT, TARGET_PROFIT, TICKER, UPPER_MULT, compute_indicators

BULLETS_MAX = 3
BULLET_SIZE = 33333.0
INITIAL_CASH = BULLETS_MAX * BULLET_SIZE
MMF_CODE = "511880"  # 银华日利 ETF


@dataclass
class PendingOrder:
    side: str  # "BUY" | "SELL"


def fetch_etf(ticker: str = TICKER) -> pd.DataFrame:
    raw = yf.download(ticker, period="max", progress=False, auto_adjust=True)
    if raw.empty:
        raise RuntimeError(f"No Yahoo data for {ticker}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw.rename(columns={"Open": "open", "Close": "close", "High": "high", "Low": "low"})
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    for col in ["open", "close", "high", "low"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[["open", "close", "high", "low"]].dropna()


def fetch_mmf_returns(code: str = MMF_CODE) -> pd.Series:
    """Daily return of 银华日利 from cumulative NAV (dividend reinvested)."""
    nav = ak.fund_open_fund_info_em(symbol=code, indicator="累计净值走势")
    nav["date"] = pd.to_datetime(nav["净值日期"])
    nav["cum_nav"] = pd.to_numeric(nav["累计净值"], errors="coerce")
    nav = nav.sort_values("date").drop_duplicates("date")
    # Drop the one-time 1.0 -> ~100 denomination jump at listing start.
    nav = nav[nav["cum_nav"] >= 50].copy()
    nav = nav.set_index("date")["cum_nav"]
    ret = nav.pct_change().fillna(0.0)
    ret.name = "mmf_ret"
    return ret


def run_backtest(df: pd.DataFrame, mmf_ret: pd.Series) -> dict:
    df = compute_indicators(df).dropna().copy()
    # Align MMF daily returns onto ETF calendar (missing -> 0 for that day).
    mmf = mmf_ret.reindex(df.index).fillna(0.0)

    mmf_value = INITIAL_CASH  # capital parked in 银华日利
    position = 0
    avg_cost = 0.0
    bullets_left = BULLETS_MAX
    pending: PendingOrder | None = None

    equity_rows: list[dict] = []
    trades: list[dict] = []

    for dt, row in df.iterrows():
        open_px = float(row["open"])
        close_px = float(row["close"])
        upper = float(row["upper"])
        lower = float(row["lower"])

        # --- fill yesterday's signal at today's open (redeem/subscribe 日利) ---
        if pending is not None:
            if pending.side == "BUY" and bullets_left > 0:
                shares = int((BULLET_SIZE / open_px) // 100) * 100
                cost = shares * open_px
                if shares > 0 and cost <= mmf_value + 1e-6:
                    new_pos = position + shares
                    avg_cost = (avg_cost * position + cost) / new_pos if new_pos else 0.0
                    position = new_pos
                    mmf_value -= cost
                    bullets_left -= 1
                    trades.append(
                        {
                            "date": dt.strftime("%Y-%m-%d"),
                            "side": "BUY",
                            "price": round(open_px, 4),
                            "shares": shares,
                            "avg_cost": round(avg_cost, 4),
                            "bullets_left": bullets_left,
                        }
                    )
            elif pending.side == "SELL" and position > 0:
                proceeds = position * open_px
                pnl = proceeds - position * avg_cost
                trades.append(
                    {
                        "date": dt.strftime("%Y-%m-%d"),
                        "side": "SELL",
                        "price": round(open_px, 4),
                        "shares": position,
                        "pnl": round(pnl, 2),
                        "return_pct": round(pnl / (position * avg_cost) * 100, 2) if avg_cost else 0.0,
                    }
                )
                mmf_value += proceeds
                position = 0
                avg_cost = 0.0
                bullets_left = BULLETS_MAX
            pending = None

        # --- evaluate signal on today's close ---
        current_return = (close_px - avg_cost) / avg_cost if position > 0 and avg_cost > 0 else None
        signal = "HOLD"
        if position > 0:
            if current_return is not None and current_return >= TARGET_PROFIT:
                signal = "SELL"
            elif close_px > upper:
                signal = "SELL"

        if signal == "HOLD" and close_px < lower and bullets_left > 0 and mmf_value >= BULLET_SIZE * 0.5:
            signal = "BUY"

        if signal == "BUY":
            pending = PendingOrder(side="BUY")
        elif signal == "SELL":
            pending = PendingOrder(side="SELL")

        # Parking capital in 银华日利 accrues that day's Nav return.
        mmf_value *= 1.0 + float(mmf.loc[dt])

        equity = mmf_value + position * close_px
        equity_rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "equity": round(equity, 2),
                "close": round(close_px, 4),
                "position": position,
                "mmf_value": round(mmf_value, 2),
            }
        )

    eq = pd.Series({r["date"]: r["equity"] for r in equity_rows}, dtype=float)
    eq.index = pd.to_datetime(eq.index)
    closes = df["close"].reindex(eq.index)

    # Buy & hold 512890 with same initial capital
    bh_shares = int((INITIAL_CASH / float(df.iloc[0]["open"])) // 100) * 100
    bh_left = INITIAL_CASH - bh_shares * float(df.iloc[0]["open"])
    # leftover scrap also parks in 日利
    bh_mmf = bh_left
    bh_eq_vals = []
    for dt in eq.index:
        bh_mmf *= 1.0 + float(mmf.loc[dt])
        bh_eq_vals.append(bh_mmf + bh_shares * float(closes.loc[dt]))
    bh_equity = pd.Series(bh_eq_vals, index=eq.index)

    # Pure 银华日利 buy&hold reference
    mmf_curve = pd.Series(dtype=float)
    v = INITIAL_CASH
    for dt in eq.index:
        v *= 1.0 + float(mmf.loc[dt])
        mmf_curve.loc[dt] = v

    def metrics(curve: pd.Series) -> dict:
        total_ret = float(curve.iloc[-1] / curve.iloc[0] - 1)
        days = (curve.index[-1] - curve.index[0]).days
        years = max(days / 365.25, 1e-9)
        cagr = float((curve.iloc[-1] / curve.iloc[0]) ** (1 / years) - 1)
        dd = curve / curve.cummax() - 1
        max_dd = float(dd.min())
        daily = curve.pct_change().dropna()
        sharpe = float(daily.mean() / daily.std() * np.sqrt(252)) if daily.std() > 0 else 0.0
        return {
            "start": curve.index[0].strftime("%Y-%m-%d"),
            "end": curve.index[-1].strftime("%Y-%m-%d"),
            "years": round(years, 2),
            "start_equity": round(float(curve.iloc[0]), 2),
            "end_equity": round(float(curve.iloc[-1]), 2),
            "total_return_pct": round(total_ret * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "sharpe": round(sharpe, 2),
        }

    yearly = []
    for year, g in eq.groupby(eq.index.year):
        yearly.append(
            {
                "year": int(year),
                "strategy_pct": round(float(g.iloc[-1] / g.iloc[0] - 1) * 100, 2),
                "buyhold_pct": round(
                    float(bh_equity.loc[g.index].iloc[-1] / bh_equity.loc[g.index].iloc[0] - 1) * 100, 2
                ),
                "mmf_pct": round(
                    float(mmf_curve.loc[g.index].iloc[-1] / mmf_curve.loc[g.index].iloc[0] - 1) * 100, 2
                ),
            }
        )

    eom = eq.resample("ME").last()
    bh_eom = bh_equity.resample("ME").last()
    mmf_eom = mmf_curve.resample("ME").last()
    step = max(1, len(eom) // 60)
    chart_idx = eom.index[::step]
    if eom.index[-1] not in chart_idx:
        chart_idx = chart_idx.append(pd.Index([eom.index[-1]]))

    buys = [t for t in trades if t["side"] == "BUY"]
    sells = [t for t in trades if t["side"] == "SELL"]
    win_sells = [t for t in sells if t.get("pnl", 0) > 0]

    # time parked in MMF vs holding ETF (by equity-days roughly: position flat days)
    flat_days = sum(1 for r in equity_rows if r["position"] == 0)
    invested_days = sum(1 for r in equity_rows if r["position"] > 0)

    return {
        "ticker": TICKER,
        "mmf": MMF_CODE,
        "params": {
            "target_profit": TARGET_PROFIT,
            "lower_mult": LOWER_MULT,
            "upper_mult": UPPER_MULT,
            "bullets": BULLETS_MAX,
            "bullet_size": BULLET_SIZE,
            "initial_cash": INITIAL_CASH,
            "fill": "next_open",
            "idle_sleeve": "511880 cumulative NAV",
        },
        "strategy": metrics(eq),
        "buy_hold": metrics(bh_equity),
        "mmf_hold": metrics(mmf_curve),
        "exposure": {
            "days_in_etf": invested_days,
            "days_in_mmf_only": flat_days,
            "mmf_only_pct": round(flat_days / max(len(equity_rows), 1) * 100, 1),
        },
        "trades": {
            "buys": len(buys),
            "sells": len(sells),
            "win_rate_pct": round(len(win_sells) / len(sells) * 100, 1) if sells else 0.0,
            "avg_sell_return_pct": round(float(np.mean([t["return_pct"] for t in sells])), 2) if sells else 0.0,
        },
        "yearly": yearly,
        "recent_trades": trades[-12:],
        "equity_chart": {
            "categories": [d.strftime("%Y-%m") for d in chart_idx],
            "strategy": [round(float(eom.loc[d]), 0) for d in chart_idx],
            "buy_hold": [round(float(bh_eom.loc[d]), 0) for d in chart_idx],
            "mmf_hold": [round(float(mmf_eom.loc[d]), 0) for d in chart_idx],
        },
        "drawdown_chart": {
            "categories": [d.strftime("%Y-%m") for d in chart_idx],
            "strategy_dd": [
                round(float((eom.loc[d] / eom.loc[:d].max() - 1) * 100), 2) for d in chart_idx
            ],
        },
    }


def main() -> None:
    etf = fetch_etf()
    mmf_ret = fetch_mmf_returns()
    result = run_backtest(etf, mmf_ret)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
