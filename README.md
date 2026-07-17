# 生活缴费系统 · Life System

一款面向社区居民的一站式公共事业缴费平台，支持 **电费 / 水费 / 燃气费** 在线缴纳、账单分类查询、阶梯计费规则查看及故障报修。

## 功能特性

- **工作台首页** — 待缴总额、本月用量、报修进度概览，近 6 月用量趋势柱状图
- **缴费中心** — 按费用类型分类，查询欠费账单并模拟支付，生成交易凭证
- **缴费记录** — 按类型（电/水/气）与状态（待缴/已缴）筛选，账单详情含阶梯计费拆分
- **计费规则** — 阶梯电价 / 水价 / 气价公开展示，附计算示例
- **故障报修** — 提交报修工单（类型 + 描述 + 紧急程度），跟踪处理进度
- **用户认证** — 注册 / 登录 / JWT 鉴权 / 路由守卫

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + TailwindCSS + Zustand + Recharts |
| 后端 | Python + Flask + Flask-SQLAlchemy + Flask-JWT-Extended |
| 数据库 | MySQL 8.0 |

## 项目结构

```
.
├── backend/                  # Python Flask 后端
│   ├── app.py                # 应用入口（工厂模式）
│   ├── config.py             # 配置（数据库/JWT）
│   ├── extensions.py         # db / jwt 实例
│   ├── models.py             # SQLAlchemy 数据模型
│   ├── schema.sql            # MySQL 建表脚本
│   ├── seed.py               # 种子数据脚本
│   ├── requirements.txt      # Python 依赖
│   ├── routes/               # API 路由
│   │   ├── auth.py           # 注册/登录/当前用户
│   │   ├── households.py     # 户号
│   │   ├── bills.py          # 账单查询/详情/支付
│   │   ├── rules.py          # 计费规则
│   │   ├── repairs.py        # 故障报修
│   │   └── dashboard.py      # 工作台概览
│   └── services/
│       └── billing.py        # 阶梯计费算法
└── src/                      # React 前端
    ├── components/           # Layout / StatCard / TypeBadge / UsageChart ...
    ├── pages/                # Login / Register / Dashboard / Payment / Records / Rules / Repair
    ├── lib/                  # axios 封装 / 常量 / 工具函数
    ├── store/                # zustand 状态管理
    └── types.ts              # TypeScript 类型定义
```

## 快速开始

### 1. 准备 MySQL

```bash
# 创建数据库与用户
mysql -u root -e "CREATE DATABASE IF NOT EXISTS life_system DEFAULT CHARSET utf8mb4;"
mysql -u root -e "CREATE USER 'life_app'@'localhost' IDENTIFIED BY 'life_pass_2026'; \
                  GRANT ALL PRIVILEGES ON life_system.* TO 'life_app'@'localhost'; FLUSH PRIVILEGES;"
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # 按需修改数据库配置
python seed.py                # 建表 + 写入演示数据
python app.py                 # 启动于 http://localhost:5000
```

### 3. 启动前端

```bash
npm install
npm run dev                   # 启动于 http://localhost:5173
```

打开 http://localhost:5173 即可使用。

## 演示账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 普通居民 | `demo` | `demo123` |
| 管理员 | `admin` | `admin123` |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/auth/me` | 当前用户 |
| GET | `/api/dashboard` | 工作台概览 |
| GET | `/api/households/mine` | 我的户号 |
| GET | `/api/bills?type=&status=` | 账单列表（分类筛选） |
| GET | `/api/bills/:id` | 账单详情（阶梯拆分） |
| POST | `/api/bills/:id/pay` | 支付账单 |
| GET | `/api/rules?type=` | 计费规则 |
| GET | `/api/repairs` | 我的报修工单 |
| POST | `/api/repairs` | 提交报修 |

## 阶梯计费示例

以电费为例（250 度）：

| 档位 | 范围 | 单价 | 用量 | 小计 |
|------|------|------|------|------|
| 第 1 档 | 0 - 180 度 | ¥0.588 | 180 | ¥105.84 |
| 第 2 档 | 181 - 400 度 | ¥0.638 | 70 | ¥44.66 |
| **合计** | | | **250** | **¥150.50** |

## License

MIT
