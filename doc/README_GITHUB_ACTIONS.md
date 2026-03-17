# 📊 Market Scanner - GitHub Actions Edition

**完全云端运行的股票数据采集工具** - 无需本地网络，每天自动更新！

---

## ✨ 核心特性

- ✅ **云端运行** - 使用 GitHub Actions，不受本地网络限制
- ✅ **完全自动** - 每天定时更新，无需手动操作
- ✅ **完全免费** - GitHub Actions 免费额度（每月 2000 分钟）
- ✅ **数据完整** - 5000+ 股票，30+ 财务指标
- ✅ **即时可用** - 数据自动提交，前端直接访问

---

## 🚀 3 步快速开始

### 1️⃣ 上传代码到 GitHub

```bash
# 克隆或创建仓库
git clone https://github.com/你的用户名/market-scanner.git
cd market-scanner

# 复制所有文件到仓库
# ├── .github/workflows/update-market-data.yml
# ├── backend/fetch_data.py
# ├── backend/requirements.txt
# ├── frontend/index.html
# └── .gitignore

git add .
git commit -m "Initial commit with GitHub Actions"
git push
```

### 2️⃣ 配置 API Keys（2 分钟）

1. 注册免费 API keys：
   - **Polygon.io**: https://polygon.io （股票列表）
   - **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html （宏观数据）

2. 添加到 GitHub Secrets：
   ```
   仓库 → Settings → Secrets and variables → Actions
   
   添加两个 secrets：
   - MASSIVE_API_KEY: 你的 Polygon key
   - FRED_API_KEY: 你的 FRED key
   ```

### 3️⃣ 手动触发首次运行

```
仓库 → Actions → Market Data Updater
→ Run workflow → 设置参数 → Run workflow
```

**建议首次参数**：
- `max_tickers`: 100（测试用）
- `request_delay`: 2.0（安全）

等待 5-10 分钟，数据就会自动更新！

---

## 📚 详细文档

- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** ⭐ 10 步部署清单
- **[GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md)** 📖 完整配置指南
- **[CONNECTION_ISSUES.md](CONNECTION_ISSUES.md)** 🔧 本地网络问题（已解决）

---

## ⏰ 运行时间

| 股票数 | 预计时间 | 每月消耗 | 免费额度 |
|--------|---------|---------|---------|
| 100 | ~5-10 分钟 | ~300 分钟 | ✅ 充足 |
| 1000 | ~30-50 分钟 | ~1500 分钟 | ✅ 够用 |
| 5000 | ~2.5-3 小时 | ~4500 分钟 | ⚠️ 需付费或减少频率 |

**建议**：
- 测试：100 股票
- 日常：1000-2000 股票
- 完整：5000 股票（每 3 天运行一次）

---

## 📊 自动化工作流

```
每天美东下午 5 点（UTC 22:00）
    ↓
GitHub Actions 启动
    ↓
云端服务器运行 Python 脚本
    ↓
从 Yahoo Finance 采集数据
    ↓
生成 market.json
    ↓
自动提交到仓库
    ↓
前端自动获取最新数据
    ↓
✅ 完成！
```

---

## 🎯 前端集成

### 方式 1：GitHub Raw URL

```javascript
const GITHUB_USER = '你的GitHub用户名';
const REPO = 'market-scanner';
const url = `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO}/main/frontend/data/market.json`;

const res = await fetch(url);
const data = await res.json();
```

### 方式 2：GitHub Pages

```
Settings → Pages → Source: main branch, /frontend folder
访问：https://你的用户名.github.io/market-scanner/
```

---

## 🔧 配置调整

### 修改运行时间

编辑 `.github/workflows/update-market-data.yml`：

```yaml
schedule:
  - cron: '0 14 * * *'  # UTC 14:00 = 美东上午 9 点
  - cron: '0 22 * * *'  # UTC 22:00 = 美东下午 5 点（推荐）
```

### 修改采集参数

```yaml
env:
  MAX_TICKERS: '5000'     # 股票数量
  REQUEST_DELAY: '2.0'    # 请求间隔（秒）
  MAX_RETRIES: '5'        # 重试次数
```

---

## 📈 获取的数据

### 估值指标
P/E, P/S, P/B, EV/EBITDA

### 盈利能力
毛利率, 营业利润率, 净利润率, FCF 利润率

### 回报率
ROE, ROA, FCF Yield

### 增长率
Revenue CAGR, EPS CAGR

### 杠杆指标
Debt/EBITDA, Debt/Equity

### 价格数据
当前价格, 涨跌幅, 成交量, 市值

---

## 🚨 故障排除

### Workflow 不运行？

1. **检查 Actions 是否启用**
   ```
   Settings → Actions → General
   确保启用 "Allow all actions"
   ```

2. **检查 Workflow 权限**
   ```
   Settings → Actions → General
   Workflow permissions: "Read and write permissions"
   ```

### 运行失败？

1. **查看日志**
   ```
   Actions → 点击失败的运行 → 查看错误步骤
   ```

2. **常见问题**：
   - ❌ Secrets 未配置 → 添加 API keys
   - ❌ 权限不足 → 调整 Workflow 权限
   - ❌ 超时 → 减少 MAX_TICKERS 或增加 timeout-minutes

### 数据未更新？

检查：
- 是否有新的提交？（🤖 Auto-update...）
- `frontend/data/market.json` 是否存在？
- Actions 是否运行成功？（绿色✅）

---

## 💡 最佳实践

1. **渐进式扩大**
   ```
   第 1 天：100 股票（测试）
   第 3 天：500 股票（验证）
   第 7 天：2000 股票（日常）
   ```

2. **监控运行**
   - 每周检查 Actions 状态
   - 确保成功率 > 95%
   - 监控免费额度使用

3. **定期优化**
   - 稳定后可降低 REQUEST_DELAY
   - 考虑增量更新（未来）
   - 添加错误通知

---

## 🎯 优势对比

| 方案 | 本地运行 | GitHub Actions ✅ |
|------|---------|------------------|
| 网络限制 | ❌ 受本地网络影响 | ✅ 云端 IP 干净 |
| 手动操作 | ❌ 需要每天运行 | ✅ 完全自动 |
| 成本 | ✅ 免费 | ✅ 免费（2000 分钟/月）|
| 稳定性 | ⚠️ 取决于本地环境 | ✅ GitHub 服务器稳定 |
| 数据访问 | ⚠️ 需要部署 | ✅ 直接访问 GitHub |

---

## 🆘 获取帮助

1. **查看详细文档** - 见上方文档链接
2. **查看 Actions 日志** - 最准确的错误信息
3. **GitHub Issues** - 提交问题
4. **社区讨论** - GitHub Discussions

---

## 📄 许可证

MIT License - 自由使用

---

## 🙏 致谢

- **GitHub Actions** - 免费云端运行环境
- **yfinance** - Yahoo Finance 数据接口
- **Polygon.io** - 股票列表 API
- **FRED** - 宏观经济数据

---

**开始使用**：查看 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) 完成 10 步部署！

Happy Automating! 🤖
