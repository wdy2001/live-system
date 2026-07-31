# 📌 生活缴费系统

## 📝 简介

面向居民用户的一站式生活缴费管理系统，支持电费/水费/燃气费在线缴费、历史记录分类查询、阶梯计费规则查看、故障报修提交与进度跟踪。

## ⚡ 技术栈

- **后端**：Python 3.9+ / FastAPI / SQLAlchemy 2.x / PyMySQL / passlib[bcrypt] / python-jose / Pydantic v2 / Uvicorn
- **前端**：React 18 / Vite 5 / Ant Design 5 / React Router v6 / Axios / dayjs
- **数据库**：MySQL 8.0+
- **测试**：Pytest + FastAPI TestClient

## 🧩 核心功能（✓ 已实现清单）

1. 用户注册/登录（JWT 鉴权 + bcrypt 密码）
2. 电费/水费/燃气费 阶梯账单查询 + 模拟缴费
3. 缴费记录按 类型/状态/日期范围 筛选 + 分页
4. 阶梯计费规则查看（电/水/气 三档）
5. 故障报修工单提交 / 取消 / 进度查看（状态：待受理/处理中/已完成/已取消）
6. 个人资料查看与修改
7. 初始化脚本一键建表 + 灌种子数据（计费规则/示例户号当月用量/演示用户demo/demo123456）

## 📁 目录结构

```
/workspace
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                   # FastAPI 入口
│   ├── init_db.py                # 一键初始化 + 种子数据
│   ├── requirements.txt          # Python 依赖
│   ├── pytest.ini                # Pytest 配置
│   ├── .env.example              # 环境变量模板
│   ├── app/
│   │   ├── config.py             # 配置
│   │   ├── database.py           # SQLAlchemy 引擎/Base/SessionLocal
│   │   ├── models.py             # 6 张表 ORM 模型
│   │   ├── core/
│   │   │   ├── security.py       # 密码 hash + JWT
│   │   │   ├── billing.py        # 阶梯+附加费计费算法
│   │   │   ├── deps.py           # get_db / get_current_user
│   │   │   └── utils.py          # 报修类型推断
│   │   ├── schemas/              # Pydantic Schemas (common/user/billing/payment/repair)
│   │   └── routers/              # auth/users/billing/payment/repair 路由
│   └── tests/                    # pytest 测试套件（13 个用例）
└── frontend/
    ├── package.json
    ├── vite.config.js            # 端口 5173 + /api 代理
    ├── index.html
    ├── .env.example
    └── src/
        ├── main.jsx              # 入口，Antd 中文 ConfigProvider
        ├── App.jsx               # 路由 + 守卫
        ├── api/                  # request.js + auth/user/billing/payment/repair
        ├── utils/                # auth.js + mapping.js(中文枚举)
        ├── layouts/MainLayout.jsx  # Sider+Header+Content 布局
        └── pages/                # Login/Register/Home/Pay/Records/Rules/RepairCreate/RepairList/Profile/NotFound
```

## 🛠️ 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Git 2.x

## 🚀 快速开始

### Step 1 克隆/进入项目

```bash
cd /workspace
```

### Step 2 准备 MySQL 数据库

在本地 MySQL 中执行：

```sql
CREATE DATABASE IF NOT EXISTS life_payment DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- 可选：创建专用用户
CREATE USER 'life_pay'@'localhost' IDENTIFIED BY 'life_pay_123';
GRANT ALL ON life_payment.* TO 'life_pay'@'localhost';
FLUSH PRIVILEGES;
```

### Step 3 配置环境变量 & 安装后端依赖

```bash
cd /workspace/backend
cp .env.example .env
# 根据实际情况修改 .env：MYSQL_HOST/MYSQL_PORT/MYSQL_USER/MYSQL_PASSWORD/MYSQL_DB/SECRET_KEY
python -m venv venv
# linux/mac:
source venv/bin/activate
# windows (PowerShell):
# venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 4 初始化数据库（建表 + 种子数据）

```bash
# 确保仍在 backend/ 目录、venv 已激活
python init_db.py
# 成功输出 "初始化完成"，会创建 6 张表、灌 9 条计费规则、3 个示例户号当月用量、demo 用户
```

### Step 5 启动后端

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# 访问：
#   健康检查：http://localhost:8000/health
#   Swagger 文档：http://localhost:8000/docs
```

### Step 6 启动前端

```bash
cd /workspace/frontend
cp .env.example .env
npm install
npm run dev
# 访问 http://localhost:5173
```

## 🧪 测试账号与演示数据

- **演示账号**：`demo` / `demo123456`（init_db 自动创建）
- **示例户号**（初始化脚本自动生成当月用量，可直接用于演示查询/缴费）：

| 户号     | 类型   | 当月用量 | 预计应缴金额（含附加费） |
|----------|--------|----------|--------------------------|
| E100001  | 电费   | 350 度   | 229.00 元                |
| W200002  | 水费   | 18 吨    | 78.00 元                 |
| G300003  | 燃气费 | 380 m³   | 1092.80 元               |

## ✅ 接口总览

| Method | 路径                          | 鉴权 | 说明                           |
|--------|-------------------------------|------|--------------------------------|
| POST   | /api/auth/register            | 否   | 用户注册                       |
| POST   | /api/auth/login               | 否   | 用户登录（获取 JWT Token）     |
| GET    | /api/users/me                 | 是   | 获取当前登录用户信息           |
| PUT    | /api/users/me                 | 是   | 修改当前登录用户资料           |
| GET    | /api/billing-rules            | 是   | 获取阶梯计费规则列表           |
| GET    | /api/meter-usage              | 是   | 查询户号当月用量               |
| POST   | /api/payments/query           | 是   | 查询账单（含阶梯计费）         |
| POST   | /api/payments/pay             | 是   | 缴纳账单                       |
| GET    | /api/payments/{id}            | 是   | 查询单条缴费记录详情           |
| GET    | /api/payments                 | 是   | 分页查询缴费记录（支持筛选）   |
| POST   | /api/repairs                  | 是   | 提交故障报修工单               |
| GET    | /api/repairs                  | 是   | 查询我的报修工单列表           |
| GET    | /api/repairs/{id}             | 是   | 查询报修工单详情               |
| POST   | /api/repairs/{id}/cancel      | 是   | 取消报修工单                   |

## 🧪 运行后端测试

```bash
cd /workspace/backend
source venv/bin/activate
pip install pytest httpx      # 已在 requirements.txt 则跳过
pytest tests -v
```

## 🔗 推送到 GitHub 步骤

```bash
cd /workspace
git init
git add .
git commit -m "feat: 初始化生活缴费系统项目"
git remote add origin <你的GitHub仓库SSH或HTTPS地址>
git branch -M main
git push -u origin main
```

> 如果还没有仓库：登录 GitHub → 右上角 + → New Repository → 名称（建议 life-payment-system）→ Create → 复制 URL 填入上面 `<...>` 再 push。

## ❓ 常见问题 FAQ

- **Q**: init_db 报 `ModuleNotFoundError: No module named 'app'`？
  **A**: 确保你是在 `backend/` 目录下执行 `python init_db.py`，脚本会自动把当前目录加入 sys.path。

- **Q**: MySQL Access denied 或 Unknown database？
  **A**: 检查 `.env` 中 `MYSQL_*` 参数是否与 Step 2 创建的一致，并确认 `life_payment` 库已创建。

- **Q**: 前端 500 或 CORS 错？
  **A**: 确认后端监听 8000 端口，CORS 中间件已允许 `http://localhost:5173`。

- **Q**: 新增户号查询 "没有 meter_usage"？
  **A**: 系统会自动为任意户号生成模拟用量数据，直接再次查询即可（`/payments/query` 接口已集成）。

## 📅 开发周期

10 天版本（MVP）。
