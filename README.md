# MARKET SCANNER

极简美股市场扫描工具 — Minecraft 字体风格，静态部署于 Cloudflare。

```
后端 Python 脚本 → market.json → 静态前端 HTML
```

---

## 架构

```
/market-scanner
├── backend/
│   ├── fetch_data.py        # 主数据抓取脚本
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html           # 单页应用（Minecraft 风格）
│   ├── data/
│   │   └── market.json      # 由后端生成，前端直接读取
│   └── _worker.js           # Cloudflare Worker 入口
├── .github/
│   └── workflows/
│       └── update_data.yml  # GitHub Actions 定时更新
└── README.md
```

---

## 数据来源

| 来源 | 用途 | API Key 来源 |
|------|------|------------|
| [Polygon.io](https://polygon.io) | 股价、基本面、上市公司列表 | polygon.io/dashboard |
| [FRED](https://fred.stlouisfed.org) | 宏观经济指标 | fred.stlouisfed.org/docs/api/api_key.html |

> Polygon 免费版限速较严，建议升级 Starter ($29/mo) 以获取全量数据。

---

## 快速开始

### 1. 配置 API Key

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 API key
```

### 2. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 3. 生成数据

```bash
# 完整运行（所有股票，可能需要数小时）
python backend/fetch_data.py

# 快速测试（100 只股票）
MAX_TICKERS=100 python backend/fetch_data.py
```

生成文件：`frontend/data/market.json`

### 4. 本地预览

```bash
# 在 frontend/ 目录下启动静态服务器
cd frontend
python -m http.server 8080
# 访问 http://localhost:8080
```

---

## 部署到 Cloudflare Pages

1. 将项目推送到 GitHub
2. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
3. Pages → Create a project → Connect to Git
4. 选择你的仓库
5. 配置：
   - **Build command**: 留空（静态文件）
   - **Build output directory**: `frontend`
6. 部署完成后，`_worker.js` 会自动作为 Worker 运行

---

## 自动化更新数据（GitHub Actions）

1. 在 GitHub 仓库 Settings → Secrets 中添加：
   - `POLYGON_API_KEY`
   - `FRED_API_KEY`

2. 每周日北京时间零点自动运行，更新 `market.json` 并推送。

也可手动触发：GitHub Actions → Update Market Data → Run workflow

---

## 指标说明

### 宏观指标

| 指标 | 来源 | 说明 |
|------|------|------|
| Fed Funds Rate | FRED FEDFUNDS | 联邦基金利率 |
| CPI YoY | FRED CPIAUCSL | 消费者物价指数同比 |
| PCE Inflation | FRED PCEPI | 个人消费支出通胀 |
| Unemployment | FRED UNRATE | 失业率 |
| GDP Growth | FRED A191RL1Q225SBEA | 实际 GDP 增速 |
| 10Y / 2Y Treasury | FRED GS10/GS2 | 国债收益率 |
| Yield Curve | 计算值 | 10Y-2Y 利差 |
| VIX | FRED VIXCLS | 恐慌指数 |

### 公司指标

| 指标 | 计算方式 | 价值投资意义 |
|------|---------|------------|
| **P/E** | Price / EPS | 市盈率，越低越便宜 |
| **EV/EBIT** | Enterprise Value / EBIT | 核心价值倍数，排除税和财务结构影响 |
| **EV/EBITDA** | EV / EBITDA | 含折旧的价值倍数 |
| **FCF Yield** | FCF / Market Cap × 100 | 自由现金流收益率，越高越好 |
| **Gross Margin** | 毛利 / 收入 × 100 | 竞争壁垒指标 |
| **Operating Margin** | 营业利润 / 收入 × 100 | 经营效率 |
| **ROIC** | EBIT×(1-税率) / 投入资本 | 资本回报率，>15% 为优秀 |
| **ROE** | 净利润 / 股东权益 | 权益回报率 |
| **Revenue CAGR** | 4年收入复合增长率 | 成长性 |
| **EPS CAGR** | 4年每股收益复合增长率 | 盈利成长性 |
| **Debt/EBITDA** | 总债务 / EBITDA | 杠杆水平，<2 为健康 |
| **Interest Coverage** | EBIT / 利息支出 | 偿债能力，>3 为安全 |

### 健康颜色说明

```
■ 深红  — 极差 (Very Poor)
■ 红    — 差   (Poor)
■ 橙    — 低于平均 (Below Avg)
■ 灰    — 中性 (Neutral)
■ 浅绿  — 良好 (Good)
■ 绿    — 优秀 (Great)
■ 亮绿  — 卓越 (Excellent)
```

---

## 注意事项

- **Polygon 免费版**：每分钟限制 5 次请求，全量 5000+ 股票需要数小时。建议用付费版或缩减 `MAX_TICKERS`。
- **数据新鲜度**：`market.json` 是快照数据，每次运行后端脚本才会更新。
- **文件大小**：5000 只股票约 15-25 MB，Cloudflare Pages 单文件限制 25 MB，如超出可分割文件。
- **FRED API**：免费，无需付费，申请即用。

---

## License

MIT
