# ✅ GitHub Actions 部署清单

## 📋 部署前准备

- [ ] 有 GitHub 账号
- [ ] 有 Polygon API Key（免费注册：https://polygon.io）
- [ ] 有 FRED API Key（免费注册：https://fred.stlouisfed.org/docs/api/api_key.html）
- [ ] 代码仓库已创建

---

## 🚀 10 步完成部署

### ☐ 第 1 步：创建仓库结构

```bash
cd market-scanner

# 创建必要的文件夹
mkdir -p .github/workflows
mkdir -p frontend/data
mkdir -p backend

# 检查结构
tree -L 3
```

---

### ☐ 第 2 步：上传文件到仓库

需要上传的文件：

```
✅ .github/workflows/update-market-data.yml
✅ backend/fetch_data.py
✅ backend/requirements.txt
✅ frontend/index.html（你的前端文件）
```

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push
```

---

### ☐ 第 3 步：配置 GitHub Secrets

1. **进入仓库设置**
   ```
   仓库页面 → Settings（顶部标签栏）
   ```

2. **添加 Secret #1**
   ```
   左侧菜单：Secrets and variables → Actions
   点击：New repository secret
   
   Name: MASSIVE_API_KEY
   Value: 粘贴你的 Polygon API key
   点击：Add secret
   ```

3. **添加 Secret #2**
   ```
   再次点击：New repository secret
   
   Name: FRED_API_KEY
   Value: 粘贴你的 FRED API key
   点击：Add secret
   ```

4. **验证 Secrets**
   ```
   确保看到两个 secrets：
   ✅ MASSIVE_API_KEY
   ✅ FRED_API_KEY
   ```

---

### ☐ 第 4 步：启用 GitHub Actions

1. **检查 Actions 是否启用**
   ```
   Settings → Actions → General
   确保 "Allow all actions and reusable workflows" 已选中
   点击 Save
   ```

2. **设置 Workflow 权限**
   ```
   在同一页面往下滚动
   找到 "Workflow permissions"
   选择 "Read and write permissions"
   勾选 "Allow GitHub Actions to create and approve pull requests"
   点击 Save
   ```

---

### ☐ 第 5 步：首次测试运行

1. **进入 Actions 标签**
   ```
   仓库页面 → Actions（顶部标签栏）
   ```

2. **手动触发 workflow**
   ```
   左侧：选择 "Market Data Updater"
   右侧：点击 "Run workflow" 下拉菜单
   
   参数设置（建议首次测试）：
   - max_tickers: 100
   - request_delay: 2.0
   
   点击绿色按钮：Run workflow
   ```

3. **等待运行**
   ```
   刷新页面，会看到一个黄色圆圈（运行中）
   点击进入查看实时日志
   ```

---

### ☐ 第 6 步：验证运行结果

运行成功后应该看到：

```
✅ 所有步骤都是绿色对勾
✅ Summary 显示：
   - Total Stocks: 100
   - Total Market Cap: $XX.XXT
   - File Size: X.X MB
```

---

### ☐ 第 7 步：检查生成的数据

1. **查看提交记录**
   ```
   仓库页面 → 顶部应该有新的提交
   提交信息：🤖 Auto-update market data - 2026-03-17 XX:XX UTC
   ```

2. **查看数据文件**
   ```
   点击 frontend/data/market.json
   文件应该存在且有内容
   ```

3. **下载 Artifact（备份）**
   ```
   Actions → 点击刚才的运行
   往下滚动 → Artifacts
   下载：market-data-X
   ```

---

### ☐ 第 8 步：配置前端读取数据

**方案 A：GitHub Raw URL（推荐）**

编辑 `frontend/index.html`：

```javascript
// 找到这行：
const res = await fetch('./data/market.json');

// 改为：
const GITHUB_USER = '你的GitHub用户名';
const REPO_NAME = 'market-scanner';
const res = await fetch(`https://raw.githubusercontent.com/${GITHUB_USER}/${REPO_NAME}/main/frontend/data/market.json`);
```

**方案 B：GitHub Pages**

```
Settings → Pages
Source: Deploy from a branch
Branch: main
Folder: /frontend
点击 Save

获得URL：https://你的用户名.github.io/market-scanner/
```

---

### ☐ 第 9 步：设置定时运行

确认 workflow 文件中的 cron 时间：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = 美东下午5-6点
```

想要修改时间？编辑这行，然后提交：

```bash
# 美东上午 9 点
- cron: '0 14 * * *'

# 美东下午 5 点（推荐）
- cron: '0 22 * * *'

# 美东晚上 9 点
- cron: '0 2 * * *'
```

---

### ☐ 第 10 步：扩大到完整数据

测试成功后，修改 workflow 默认值：

编辑 `.github/workflows/update-market-data.yml`：

```yaml
env:
  MAX_TICKERS: '5000'      # 从 100 改为 5000
  REQUEST_DELAY: '2.0'     # 保持 2.0
```

提交并等待下次自动运行，或手动触发。

---

## 🎯 完成检查

全部完成后，你应该有：

- ✅ GitHub Actions 每天自动运行
- ✅ 数据自动更新到 `market.json`
- ✅ 前端可以访问最新数据
- ✅ 无需本地网络，完全在云端运行

---

## 📊 监控和维护

### 每周检查一次：

1. **Actions 运行状态**
   ```
   Actions → 查看最近几次运行
   确保都是绿色✅
   ```

2. **错误率**
   ```
   点击运行详情 → 查看 Summary
   Skipped 数量应该 < 5%
   ```

3. **免费额度使用**
   ```
   Settings → Billing and plans
   查看 Actions minutes used
   确保在限额内
   ```

### 出现问题时：

1. **查看运行日志**
   ```
   Actions → 点击失败的运行 → 查看红叉步骤
   ```

2. **常见问题**：
   - API Key 错误 → 检查 Secrets
   - 超时 → 增加 REQUEST_DELAY
   - Git 推送失败 → 检查 Workflow 权限

3. **手动修复**：
   ```
   下载最新代码
   本地运行 fetch_data.py
   手动提交 market.json
   ```

---

## 💡 优化建议

### 1 周后：

- [ ] 如果运行稳定，可以将 `REQUEST_DELAY` 从 2.0 降到 1.5
- [ ] 增加 `MAX_TICKERS` 到完整的 5000

### 1 个月后：

- [ ] 考虑添加错误通知（Slack/Email）
- [ ] 设置数据备份策略
- [ ] 优化为增量更新（只更新变化的股票）

---

## 🆘 需要帮助？

遇到问题时的检查顺序：

1. **查看 GITHUB_ACTIONS_GUIDE.md** - 详细文档
2. **查看 GitHub Actions 日志** - 找具体错误
3. **检查 Secrets 配置** - 最常见的问题
4. **验证文件路径** - 确保结构正确
5. **GitHub Issues** - 提交问题

---

恭喜！🎉 你已经完成了 GitHub Actions 云端部署！

现在可以：
- ☕ 喝杯咖啡，等待第一次自动运行
- 📊 查看前端页面是否显示数据
- 🔔 设置通知，监控运行状态

**记住**：GitHub Actions 会在后台默默工作，每天为你更新数据！
