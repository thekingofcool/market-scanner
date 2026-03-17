# 📁 文件组织指南

## 🎯 完整的仓库结构

将下载的文件按以下结构组织到你的 GitHub 仓库：

```
market-scanner/                        # 你的仓库根目录
│
├── .github/                           
│   └── workflows/
│       └── update-market-data.yml     ← GitHub Actions 配置
│
├── backend/
│   ├── fetch_data.py                  ← 数据采集脚本
│   └── requirements.txt               ← Python 依赖
│
├── frontend/
│   ├── index.html                     ← 前端页面
│   └── data/
│       └── market.json                ← 生成的数据（自动创建）
│
├── .gitignore                         ← Git 忽略文件
│
└── README.md                          ← 主文档
    (使用 README_GITHUB_ACTIONS.md 的内容)
```

---

## 📦 文件清单

### ✅ 必需文件（核心功能）

1. **`.github/workflows/update-market-data.yml`**
   - 作用：GitHub Actions 工作流配置
   - 位置：`.github/workflows/` 目录下
   - 说明：定时运行数据采集任务

2. **`backend/fetch_data.py`**
   - 作用：Python 数据采集脚本
   - 位置：`backend/` 目录下
   - 说明：从 Yahoo Finance 获取股票数据

3. **`backend/requirements.txt`**
   - 作用：Python 依赖列表
   - 位置：`backend/` 目录下
   - 说明：GitHub Actions 自动安装依赖

4. **`frontend/index.html`**
   - 作用：前端展示页面
   - 位置：`frontend/` 目录下
   - 说明：你现有的前端文件

5. **`.gitignore`**
   - 作用：防止敏感文件提交
   - 位置：仓库根目录
   - 说明：包含 `.env` 等忽略规则

---

### 📚 文档文件（推荐但可选）

6. **`README.md`**
   - 建议使用：`README_GITHUB_ACTIONS.md` 的内容
   - 位置：仓库根目录
   - 作用：项目主文档

7. **`DEPLOYMENT_CHECKLIST.md`**
   - 位置：仓库根目录或 `docs/` 目录
   - 作用：10 步部署清单

8. **`GITHUB_ACTIONS_GUIDE.md`**
   - 位置：仓库根目录或 `docs/` 目录
   - 作用：详细配置指南

---

## 🚀 快速部署步骤

### 方式 A：从头创建（推荐）

```bash
# 1. 创建新仓库
mkdir market-scanner
cd market-scanner
git init

# 2. 创建目录结构
mkdir -p .github/workflows
mkdir -p backend
mkdir -p frontend/data

# 3. 复制文件到对应位置
# 将下载的文件移动到上述目录

# 4. 提交到 GitHub
git add .
git commit -m "Initial commit with GitHub Actions"
git remote add origin https://github.com/你的用户名/market-scanner.git
git push -u origin main
```

### 方式 B：更新现有仓库

```bash
# 1. 进入现有仓库
cd market-scanner

# 2. 创建必要目录
mkdir -p .github/workflows
mkdir -p backend

# 3. 添加新文件
# 将 update-market-data.yml 放到 .github/workflows/
# 将 fetch_data.py 和 requirements.txt 放到 backend/
# 将 .gitignore 放到根目录

# 4. 提交更新
git add .
git commit -m "Add GitHub Actions workflow"
git push
```

---

## 📝 前端文件修改

修改 `frontend/index.html` 中的数据加载路径：

### 找到这段代码：
```javascript
async function init() {
  try {
    const res = await fetch('./data/market.json');
    // ...
```

### 改为：
```javascript
async function init() {
  try {
    // GitHub Raw URL 方式
    const GITHUB_USER = '你的GitHub用户名';  // ← 改成你的用户名
    const REPO = 'market-scanner';
    const url = `https://raw.githubusercontent.com/${GITHUB_USER}/${REPO}/main/frontend/data/market.json`;
    
    const res = await fetch(url);
    // ...
```

或者使用 GitHub Pages（需要在 Settings 中启用）：
```javascript
const res = await fetch('https://你的用户名.github.io/market-scanner/data/market.json');
```

---

## 🔐 配置 GitHub Secrets

**在上传代码后，必须配置以下 Secrets**：

```
仓库页面 → Settings → Secrets and variables → Actions

添加 2 个 repository secrets：

1. Name: MASSIVE_API_KEY
   Value: 你的 Polygon.io API key

2. Name: FRED_API_KEY
   Value: 你的 FRED API key
```

**没有配置 Secrets 会导致 workflow 失败！**

---

## ✅ 验证清单

上传完成后，检查：

- [ ] `.github/workflows/update-market-data.yml` 存在
- [ ] `backend/fetch_data.py` 存在
- [ ] `backend/requirements.txt` 存在
- [ ] `frontend/index.html` 存在
- [ ] `.gitignore` 存在
- [ ] GitHub Secrets 已配置（MASSIVE_API_KEY, FRED_API_KEY）
- [ ] Actions 已启用（Settings → Actions → General）
- [ ] Workflow 权限设置为 "Read and write"

---

## 🎯 首次运行

所有文件上传并配置好后：

```
1. 进入仓库 Actions 标签
2. 选择 "Market Data Updater"
3. 点击 "Run workflow"
4. 设置参数：
   - max_tickers: 100
   - request_delay: 2.0
5. 点击绿色按钮运行

等待 5-10 分钟，查看结果！
```

---

## 📖 后续步骤

1. **阅读文档**：
   - `DEPLOYMENT_CHECKLIST.md` - 详细部署步骤
   - `GITHUB_ACTIONS_GUIDE.md` - 高级配置

2. **测试验证**：
   - 检查 Actions 运行状态
   - 验证 `market.json` 已生成
   - 测试前端页面

3. **扩大规模**：
   - 首次成功后，增加 `MAX_TICKERS`
   - 优化 `REQUEST_DELAY`
   - 设置定时运行

---

## 🆘 遇到问题？

**按顺序检查**：

1. ✅ 文件结构是否正确？
2. ✅ Secrets 是否已配置？
3. ✅ Actions 是否已启用？
4. ✅ Workflow 权限是否正确？
5. 📋 查看 Actions 运行日志

**仍然有问题**：
- 查看 `GITHUB_ACTIONS_GUIDE.md` 的故障排除章节
- 检查 Actions 标签中的详细日志
- GitHub Issues 提交问题

---

好运！🚀 GitHub Actions 会在云端为你自动运行！
