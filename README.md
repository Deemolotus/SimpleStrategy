# 红利低波 ETF 实盘信号 (Streamlit)

基于 **512890 红利低波 ETF** 的 20 日布林带策略信号工具。  
在浏览器中填写持仓状态，一键获取买入 / 卖出 / 持仓建议。

数据来源：[Yahoo Finance](https://finance.yahoo.com/)（通过 `yfinance`）。

> **免责声明**：本工具仅供学习与研究，不构成任何投资建议。历史信号不保证未来收益，请自行承担交易风险。

[English](README.en.md)

## 策略规则

| 条件 | 信号 |
|------|------|
| 持仓且收益率 ≥ 10% | 🔴 清仓卖出 |
| 持仓且收盘价 > 2.0× 上轨 | 🔴 清仓卖出 |
| 收盘价 < 2.2× 下轨 且仍有子弹 | 🟢 加仓买入 |
| 其他 | 🟡 持仓等待 / 空仓等待 |

布林带为**非对称**设置：下轨用 `2.2×` 标准差，上轨用 `2.0×`。买入按最多 3 发「子弹」分批加仓。

无加仓机会时，未投入资金默认轮动至 **银华日利 ETF（511880）**，而非闲置现金。

## 回测结果

脚本：[backtest.py](backtest.py)。区间约 **2019-02-13 → 2026-08-10**（Yahoo 上 512890 有数据的最长历史）。

设定摘要：收盘出信号、次日开盘成交；本金 3×¥33,333；空仓段按 511880 **累计净值**计息（行情成交价会严重低估货基收益）。

| | 策略（低波 ↔ 日利） | 死拿 512890 | 纯拿 511880 |
|--|--|--|--|
| 总收益 | **+88.1%** | +121.1% | +10.8% |
| 年化 CAGR | **8.8%** | 11.2% | 1.4% |
| 最大回撤 | **-3.7%** | -16.5% | ~0% |
| Sharpe | **1.61** | 0.73 | — |

补充：约 **70%** 交易日满仓日利；清仓 18 次、胜率 100%、平均出场约 +5.3%（不少为上轨卖出，未等到 10% 硬止盈）。

复现：

```bash
python backtest.py
```

> 历史回测仅供研究，不构成投资建议；未计入交易成本、滑点与税费。

## 本地运行

### 1. 安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run streamlit_app.py
```

浏览器会自动打开 `http://localhost:8501`。

## 项目结构

```
.
├── streamlit_app.py    # Streamlit 主入口
├── strategy.py         # 数据获取与信号逻辑
├── backtest.py         # 低波 ↔ 银华日利轮动回测
├── requirements.txt
├── LICENSE             # MIT
├── README.md           # 中文（本文件）
├── README.en.md        # English
└── .github/workflows/  # 可选：Streamlit 保活定时任务
```

## 常见问题

**Q: 部署后显示 "数据获取失败"？**  
A: Streamlit Cloud 服务器需要能访问 Yahoo Finance。偶发 API 限流时，稍后重试即可。

**Q: 需要配置 secrets 吗？**  
A: 不需要。本应用不使用 API Key 或数据库。

**Q: 如何修改策略参数？**  
A: 编辑 `strategy.py` 中的 `TARGET_PROFIT`、`LOWER_MULT`、`UPPER_MULT`，然后重新部署即可。

## License

[MIT](LICENSE)
