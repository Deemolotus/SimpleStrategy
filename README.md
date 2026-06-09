# 红利低波 ETF 实盘信号 (Streamlit)

基于 **512890 红利低波 ETF** 的 20 日布林带策略信号工具。  
在浏览器中填写持仓状态，一键获取买入 / 卖出 / 持仓建议。

数据来源：[Yahoo Finance](https://finance.yahoo.com/)（通过 `yfinance`）。

> **免责声明**：本工具仅供学习与研究，不构成任何投资建议。历史信号不保证未来收益，请自行承担交易风险。

## 策略规则

| 条件 | 信号 |
|------|------|
| 持仓且收益率 ≥ 10% | 🔴 清仓卖出 |
| 持仓且收盘价 > 2.0× 上轨 | 🔴 清仓卖出 |
| 收盘价 < 2.2× 下轨 且仍有子弹 | 🟢 加仓买入 |
| 其他 | 🟡 持仓等待 / 空仓等待 |

## 本地运行

### 1. 安装依赖

```bash
cd streamlit-app
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

## 部署到 Streamlit Community Cloud

[Streamlit Community Cloud](https://share.streamlit.io/) 提供免费托管，适合公开分享。

### 步骤 1：上传到 GitHub

**方式 A — 单独仓库（推荐）**

1. 在 GitHub 新建一个仓库，例如 `dividend-low-vol-signal`。
2. 将 `streamlit-app/` 文件夹内的**全部文件**复制到仓库根目录（不要嵌套在子文件夹里）。
3. 提交并 push：

```bash
git init
git add .
git commit -m "Add Streamlit signal app for 512890 ETF"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**方式 B — 作为 monorepo 子目录**

也可以保留在 `Crowdness/Astock/streamlit-app/` 路径下，部署时在 Streamlit 设置里指定子目录即可（见下方）。

### 步骤 2：连接 Streamlit Cloud

1. 打开 [share.streamlit.io](https://share.streamlit.io/) 并用 GitHub 登录。
2. 点击 **New app**。
3. 填写：
   - **Repository**：你的 GitHub 仓库
   - **Branch**：`main`
   - **Main file path**：
     - 若文件在仓库根目录：`streamlit_app.py`
     - 若在 monorepo 子目录：`Crowdness/Astock/streamlit-app/streamlit_app.py`
4. 点击 **Deploy**。

首次部署约需 2–5 分钟。完成后会得到一个公开 URL，例如：

```
https://your-app-name.streamlit.app
```

### 步骤 3：分享

把 Streamlit 提供的链接发给其他人即可，无需安装 Python 或 exe。

## 项目结构

```
streamlit-app/
├── streamlit_app.py    # Streamlit 主入口（部署时指定此文件）
├── strategy.py         # 数据获取与信号逻辑
├── requirements.txt    # Python 依赖
├── LICENSE             # MIT 许可证
├── README.md           # 本文件
├── .gitignore
└── .streamlit/
    └── config.toml     # 主题与服务器配置
```

## 与桌面版 exe 的关系

同目录下的 `../实盘信号.py` 是 Windows 桌面版（PyInstaller 打包）。  
Streamlit 版复用了相同的策略逻辑，但增加了：

- 浏览器 UI 与侧边栏参数输入
- 近 60 日价格 / 布林带走势图
- 在线公开访问，无需下载 exe

## 常见问题

**Q: 部署后显示 "数据获取失败"？**  
A: Streamlit Cloud 服务器需要能访问 Yahoo Finance。偶发 API 限流时，稍后重试即可。

**Q: 需要配置 secrets 吗？**  
A: 不需要。本应用不使用 API Key 或数据库。

**Q: 如何修改策略参数？**  
A: 编辑 `strategy.py` 中的 `TARGET_PROFIT`、`LOWER_MULT`、`UPPER_MULT`，然后 push 到 GitHub，Streamlit 会自动重新部署。

## License

[MIT](LICENSE)
