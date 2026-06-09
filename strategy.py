"""Bollinger-band signal logic for 红利低波 ETF (512890)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal

import pandas as pd
import yfinance as yf

TICKER = "512890.SS"
TARGET_PROFIT = 0.10
LOWER_MULT = 2.2
UPPER_MULT = 2.0

SignalType = Literal["BUY", "SELL", "HOLD"]


@dataclass
class AccountState:
    position: int = 0
    avg_cost: float = 0.0
    bullets_left: int = 3
    bullet_size_rmb: float = 33333.0


@dataclass
class SignalResult:
    signal: SignalType
    message: str
    detail: str
    trade_date: str
    close: float
    upper: float
    lower: float
    ma20: float
    current_return: float | None = None
    buy_shares: int | None = None


def fetch_data(ticker: str = TICKER, retries: int = 3) -> pd.DataFrame:
    """Fetch daily OHLC data from Yahoo Finance."""
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            df = yf.download(ticker, period="90d", progress=False, auto_adjust=True)
            if df.empty:
                raise ValueError("No data returned. Market may be closed or the API is unavailable.")

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.rename(columns={
                "Open": "open",
                "Close": "close",
                "High": "high",
                "Low": "low",
            })
            df.index = pd.to_datetime(df.index)
            df.index.name = "date"

            for col in ["open", "close", "high", "low"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df[["open", "close", "high", "low"]].dropna()
            if len(df) < 20:
                raise ValueError(f"Not enough history ({len(df)} days) to compute 20-day bands.")

            return df

        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(3)

    raise RuntimeError(f"Failed after {retries} attempts: {last_error}")


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ma20"] = out["close"].rolling(window=20).mean()
    out["std20"] = out["close"].rolling(window=20).std()
    out["upper"] = out["ma20"] + UPPER_MULT * out["std20"]
    out["lower"] = out["ma20"] - LOWER_MULT * out["std20"]
    return out


def evaluate_signal(df: pd.DataFrame, account: AccountState) -> SignalResult:
    latest = df.iloc[-1]
    trade_date = latest.name.strftime("%Y-%m-%d")
    close = float(latest["close"])
    upper = float(latest["upper"])
    lower = float(latest["lower"])
    ma20 = float(latest["ma20"])

    current_return = None
    if account.position > 0 and account.avg_cost > 0:
        current_return = (close - account.avg_cost) / account.avg_cost

    if account.position > 0:
        if current_return is not None and current_return >= TARGET_PROFIT:
            return SignalResult(
                signal="SELL",
                message="清仓卖出",
                detail=f"已触发 {TARGET_PROFIT:.0%} 硬止盈目标，建议明日开盘获利了结。",
                trade_date=trade_date,
                close=close,
                upper=upper,
                lower=lower,
                ma20=ma20,
                current_return=current_return,
            )
        if close > upper:
            return SignalResult(
                signal="SELL",
                message="清仓卖出",
                detail="收盘价突破布林带上轨，动能过热，建议明日开盘高抛落袋。",
                trade_date=trade_date,
                close=close,
                upper=upper,
                lower=lower,
                ma20=ma20,
                current_return=current_return,
            )

    if close < lower and account.bullets_left > 0:
        buy_shares = int((account.bullet_size_rmb / close) // 100) * 100
        return SignalResult(
            signal="BUY",
            message="加仓买入",
            detail=(
                f"跌破 {LOWER_MULT}x 下轨，触发抄底信号。"
                f"建议明日开盘买入约 {buy_shares} 股，剩余子弹 {account.bullets_left - 1} 发。"
            ),
            trade_date=trade_date,
            close=close,
            upper=upper,
            lower=lower,
            ma20=ma20,
            current_return=current_return,
            buy_shares=buy_shares,
        )

    if account.position > 0:
        return SignalResult(
            signal="HOLD",
            message="装死持仓",
            detail="未触发止盈或加仓信号，继续耐心等待。",
            trade_date=trade_date,
            close=close,
            upper=upper,
            lower=lower,
            ma20=ma20,
            current_return=current_return,
        )

    return SignalResult(
        signal="HOLD",
        message="空仓等待",
        detail="暂无交易机会，红利低波风平浪静。空仓可持有货币基金，明天见。",
        trade_date=trade_date,
        close=close,
        upper=upper,
        lower=lower,
        ma20=ma20,
        current_return=current_return,
    )
