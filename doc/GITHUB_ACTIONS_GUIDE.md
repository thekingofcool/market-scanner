# 🚀 GitHub Actions 云端数据采集方案

## 📋 方案概述

使用 GitHub Actions 在云端自动运行数据采集，完美解决本地网络问题：

✅ **优势**：
- 使用 GitHub 云端服务器（IP 干净，不会被限制）
- 每天自动定时运行，无需手动操作
- 免费额度：每月 2000 分钟（5000 股票约 150 分钟，足够每天运行）
- 数据自动提交到仓库，前端直接使用
- 可以手动触发，方便测试

⏰ **时间消耗**：
- 100 股票：~5-10 分钟
- 1000 股票：~30-50 分钟
- 5000 股票：~2.5-3 小时

---

## 🎯 完整部署步骤

### 第 1 步：准备仓库结构

确保你的 GitHub 仓库有以下结构：

```
market-scanner/
├── .github/
│   └── workflows/
│       └── update-market-data.yml  ← GitHub Actions 配置
├── backend/
│   ├── fetch_data.py              ← 数据采集脚本
│   └── requirements.txt           ← Python 依赖（可选）
└── frontend/
    └── data/
        └── market.json            ← 生成的数据（会自动创建）
```

### 第 2 步：上传 GitHub Actions 配置

1. 在你的仓库根目录创建文件夹结构：
   ```bash
   mkdir -p .github/workflows
   ```

2. 上传 `update-market-data.yml` 到 `.github/workflows/` 目录

3. 提交并推送：
   ```bash
   git add .github/workflows/update-market-data.yml
   git commit -m "Add GitHub Actions workflow for market data"
   git push
   ```

---

### 第 3 步：配置 GitHub Secrets（重要！）

GitHub Actions 需要你的 API keys，但不能直接写在代码里。需要设置 Secrets：

#### 操作步骤：

1. **进入仓库设置**
   - 打开你的 GitHub 仓库
   - 点击 `Settings` （设置）

2. **添加 Secrets**
   - 左侧菜单找到 `Secrets and variables` → `Actions`
   - 点击 `New repository secret`

3. **添加以下 Secrets**：

   **Secret 1: MASSIVE_API_KEY**
   - Name: `MASSIVE_API_KEY`
   - Value: 你的 Polygon API key
   - 点击 `Add secret`

   **Secret 2: FRED_API_KEY**
   - Name: `FRED_API_KEY`
   - Value: 你的 FRED API key
   - 点击 `Add secret`

#### 配置截图位置：
```
仓库首页 → Settings → 
  左侧菜单: Secrets and variables → Actions → 
    New repository secret
```

---

### 第 4 步：测试运行

#### 方法 A：手动触发（推荐先测试）

1. 进入仓库的 `Actions` 标签
2. 左侧选择 `Market Data Updater`
3. 点击右侧 `Run workflow` 下拉菜单
4. 可以自定义参数：
   - `max_tickers`: 测试建议先用 `100`
   - `request_delay`: 建议 `2.0`
5. 点击绿色的 `Run workflow` 按钮

#### 方法 B：等待定时运行

工作流配置为每天 UTC 22:00（美东下午 5-6 点）自动运行。

---

### 第 5 步：监控运行状态

#### 查看运行进度：

1. 进入 `Actions` 标签
2. 点击最新的运行记录
3. 可以实时查看日志输出

#### 运行成功标志：

- ✅ 所有步骤都是绿色对勾
- ✅ 看到提交记录 "🤖 Auto-update market data"
- ✅ `frontend/data/market.json` 文件已更新

#### 查看数据：

运行成功后，可以直接访问：
```
https://github.com/你的用户名/market-scanner/blob/main/frontend/data/market.json
```

---

## ⚙️  配置说明

### 定时运行时间

在 `update-market-data.yml` 中修改 cron 表达式：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = 美东 17:00/18:00
```

常用时间：
- `'0 14 * * *'` - UTC 14:00 = 美东 9:00/10:00（开盘前）
- `'0 22 * * *'` - UTC 22:00 = 美东 17:00/18:00（收盘后，推荐）
- `'0 2 * * *'`  - UTC 02:00 = 美东 21:00/22:00（深夜）

**提示**：使用 [crontab.guru](https://crontab.guru/) 帮助设置 cron 表达式

### 调整采集参数

修改 workflow 文件中的默认值：

```yaml
env:
  MAX_TICKERS: '5000'     # 改为你想要的数量
  REQUEST_DELAY: '2.0'    # 增加到 3.0 更保守
  MAX_RETRIES: '5'        # 重试次数
```

---

## 🎯 GitHub Actions 免费额度

| 账户类型 | 每月免费分钟 | 并发任务 |
|---------|------------|---------|
| **Free** | 2000 分钟 | 20 |
| **Pro** | 3000 分钟 | 40 |
| **Team** | 3000 分钟 | 60 |

**你的使用量**：
- 100 股票：~10 分钟 → 每月可运行 200 次
- 1000 股票：~50 分钟 → 每月可运行 40 次
- 5000 股票：~150 分钟 → 每月可运行 13 次

**每天运行一次完全够用！** ✅

---

## 🔧 高级配置

### 1. 多个定时任务

如果想要一天运行多次：

```yaml
schedule:
  - cron: '0 14 * * *'  # 美东上午
  - cron: '0 22 * * *'  # 美东下午
```

### 2. 只在工作日运行

```yaml
schedule:
  - cron: '0 22 * * 1-5'  # 周一到周五
```

### 3. 不同参数的多个任务

创建 `update-market-data-full.yml` 和 `update-market-data-quick.yml`：

**Quick 版本**（每小时）：
```yaml
schedule:
  - cron: '0 * * * *'  # 每小时
env:
  MAX_TICKERS: '100'   # 只更新 100 只大盘股
  REQUEST_DELAY: '1.5'
```

**Full 版本**（每天）：
```yaml
schedule:
  - cron: '0 22 * * *'  # 每天一次
env:
  MAX_TICKERS: '5000'  # 完整数据
  REQUEST_DELAY: '2.0'
```

### 4. 添加通知

失败时发送通知（需要配置 Slack/Discord webhook）：

```yaml
- name: Notify on failure
  if: failure()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-Type: application/json' \
      -d '{"text":"❌ Market data update failed!"}'
```

---

## 📊 前端集成

### 方案 A：直接从 GitHub 读取（推荐）

前端 HTML 修改：

```javascript
// 原来：
const res = await fetch('./data/market.json');

// 改为（使用 GitHub raw URL）：
const res = await fetch('https://raw.githubusercontent.com/你的用户名/market-scanner/main/frontend/data/market.json');
```

### 方案 B：使用 GitHub Pages

1. 仓库 Settings → Pages
2. Source 选择 `main` 分支，目录选择 `/frontend`
3. 保存后获得 URL：`https://你的用户名.github.io/market-scanner/`
4. 数据 URL：`https://你的用户名.github.io/market-scanner/data/market.json`

### 方案 C：配置 CORS（如果需要）

在 workflow 中添加 `_headers` 文件（Cloudflare Pages / Netlify）：

```yaml
- name: Add CORS headers
  run: |
    cat > frontend/_headers << EOF
    /data/*
      Access-Control-Allow-Origin: *
    EOF
```

---

## 🚨 故障排除

### 问题 1：Workflow 没有运行

**检查**：
- GitHub Actions 是否启用？（Settings → Actions → General → 确保启用）
- Secrets 是否正确配置？
- cron 时间是否正确？

**解决**：
- 手动触发一次测试
- 查看 Actions 标签是否有错误信息

### 问题 2：运行失败

**常见原因**：
1. **Secrets 未配置** - 检查 API keys
2. **网络超时** - 增加 `REQUEST_DELAY`
3. **依赖安装失败** - 检查 `requirements.txt`
4. **数据未提交** - 检查 git 配置

**查看详细日志**：
- Actions → 点击失败的运行 → 查看红色 ✗ 的步骤

### 问题 3：数据没有更新到仓库

**检查**：
```yaml
- name: Commit and push changes
  run: |
    git config --local user.email "github-actions[bot]@users.noreply.github.com"
    git config --local user.name "github-actions[bot]"
```

确保这段代码在 workflow 中。

### 问题 4：超过免费额度

**症状**：Workflow 显示 "billing limit"

**解决**：
1. 减少 `MAX_TICKERS`
2. 增加 `REQUEST_DELAY`（更快完成）
3. 只在特定时间运行（如周末）

---

## 💡 最佳实践

### 1. 渐进式启动

```
第 1 天：MAX_TICKERS=100，测试流程
第 2 天：MAX_TICKERS=500，验证稳定性
第 3 天：MAX_TICKERS=1000
第 7 天：MAX_TICKERS=5000，正式运行
```

### 2. 监控和日志

定期检查：
- Actions 成功率
- 运行时间趋势
- 错误率（应 < 5%）

### 3. 备份策略

工作流自动保留最近 7 天的数据作为 Artifact：
- Actions → 选择运行 → Artifacts → 下载备份

### 4. 版本控制

在 `market.json` 中保留版本信息：
```json
{
  "meta": {
    "version": "1.1",
    "generated_at": "2026-03-17T...",
    "generated_by": "github-actions"
  }
}
```

---

## 📈 性能优化

### 当前配置（保守）：
```yaml
REQUEST_DELAY: '2.0'    # 每秒 0.5 个请求
MAX_RETRIES: '5'        # 5 次重试
```

### 激进配置（风险更高）：
```yaml
REQUEST_DELAY: '1.0'    # 每秒 1 个请求
MAX_RETRIES: '3'        # 3 次重试
```

**建议**：
- 首次运行使用保守配置
- 稳定运行一周后可以尝试优化
- 监控错误率，保持在 5% 以下

---

## 🎯 总结

使用 GitHub Actions 方案，你可以：

✅ **完全解决本地网络问题**
✅ **自动化日常更新，无需手动操作**
✅ **免费额度充足，每天运行无压力**
✅ **数据自动提交，前端直接使用**
✅ **可随时手动触发，方便测试**

**下一步**：按照上面的步骤设置 GitHub Actions，然后手动触发第一次运行！

有任何问题随时告诉我！🚀
