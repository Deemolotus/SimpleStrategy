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
