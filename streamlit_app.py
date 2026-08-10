"""Streamlit app: 红利低波 (512890) Bollinger-band trading signals."""

from __future__ import annotations

import streamlit as st

from strategy import (
    LOWER_MULT,
    TICKER,
    UPPER_MULT,
    AccountState,
    compute_indicators,
    evaluate_signal,
    fetch_data,
)

st.set_page_config(
    page_title="红利低波信号 | 512890",
    page_icon="📈",
    layout="wide",
)

# Map signal type -> (emoji, Streamlit callout method name)
SIGNAL_STYLE = {
    "BUY": ("🟢", "success"),
    "SELL": ("🔴", "error"),
    "HOLD": ("🟡", "info"),
}


def main() -> None:
    st.title("红利低波 ETF 实盘信号")
    st.caption("512890 · 20 日布林带策略 · 数据来源 Yahoo Finance")

    # Sidebar: account state the user must fill in before requesting a signal.
    with st.sidebar:
        st.header("账户状态")
        position = st.number_input("当前持股 (股)", min_value=0, value=0, step=100)
        avg_cost = st.number_input("持仓成本 (元)", min_value=0.0, value=0.0, step=0.001, format="%.3f")
        bullets_left = st.slider("剩余子弹 (次)", min_value=0, max_value=3, value=3)
        bullet_size = st.number_input("单发金额 (元)", min_value=1000, value=33333, step=1000)

        st.divider()
        st.markdown(
            "**策略规则**\n\n"
            f"- 卖出：收益 ≥ 10% 或收盘价 > {UPPER_MULT}x 上轨\n"
            f"- 买入：收盘价 < {LOWER_MULT}x 下轨 且仍有子弹\n"
            "- 其余：持仓或空仓等待"
        )
        run = st.button("刷新信号", type="primary", use_container_width=True)

    account = AccountState(
        position=int(position),
        avg_cost=float(avg_cost),
        bullets_left=int(bullets_left),
        bullet_size_rmb=float(bullet_size),
    )

    # First visit with no prior result: prompt the user instead of auto-fetching.
    if not run and "last_result" not in st.session_state:
        st.info("在左侧填写账户状态，然后点击 **刷新信号** 获取最新指令。")
        return

    with st.spinner("正在从 Yahoo Finance 获取 512890 行情..."):
        try:
            df = fetch_data(TICKER)
            df = compute_indicators(df)
            result = evaluate_signal(df, account)
            # Cache so UI widgets can re-render without requiring another click.
            st.session_state["last_result"] = result
            st.session_state["last_df"] = df
        except Exception as exc:
            st.error(f"数据获取失败：{exc}")
            return

    result = st.session_state["last_result"]
    df = st.session_state["last_df"]
    emoji, level = SIGNAL_STYLE[result.signal]
    banner = getattr(st, level)

    banner(f"{emoji} **{result.message}** — {result.detail}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("交易日", result.trade_date)
    c2.metric("收盘价", f"{result.close:.3f}")
    c3.metric(f"上轨 ({UPPER_MULT}x)", f"{result.upper:.3f}")
    c4.metric(f"下轨 ({LOWER_MULT}x)", f"{result.lower:.3f}")

    if result.current_return is not None:
        st.metric("当前持仓收益率", f"{result.current_return * 100:.2f}%")
    if result.buy_shares is not None:
        st.metric("建议买入股数", f"{result.buy_shares} 股")

    st.subheader("近 60 日走势")
    chart_df = df.tail(60)[["close", "upper", "lower", "ma20"]].rename(
        columns={"close": "收盘", "upper": "上轨", "lower": "下轨", "ma20": "MA20"}
    )
    st.line_chart(chart_df, height=360)

    with st.expander("查看原始数据"):
        show_df = df.tail(30)[["open", "high", "low", "close", "ma20", "upper", "lower"]].copy()
        show_df.index = show_df.index.strftime("%Y-%m-%d")
        st.dataframe(show_df.round(3), use_container_width=True)

    st.caption(
        "免责声明：本工具仅供学习与研究，不构成投资建议。"
        "历史信号不保证未来收益，请自行承担交易风险。"
    )


if __name__ == "__main__":
    main()
