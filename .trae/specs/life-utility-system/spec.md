# 生活缴费系统 - Product Requirement Document

## Overview
- **Summary**: 构建一个面向居民用户的生活缴费一站式服务平台，集成电费、水费、燃气费的在线查询与缴费、分类缴费记录查询、阶梯计费规则展示、故障报修等核心功能。后端采用 Python Flask + MySQL，前端采用 React + TypeScript + Vite，整体采用前后端分离架构。
- **Purpose**: 解决居民用户日常生活中需要分别前往不同营业厅或多个 APP 才能完成水电燃气缴费与报修的痛点，提供统一、便捷、透明的在线生活服务入口。
- **Target Users**: 城市居民家庭用户（普通住户）、物业管理相关人员（通过管理员角色）

## Goals
- 实现电费、水费、燃气费三类费用的账单查询与在线模拟缴费
- 实现按费用类型、缴费状态分类查看历史缴费记录与账单明细
- 实现阶梯计费规则的可视化展示与费用计算说明
- 实现故障报修工单的提交、进度查询与状态流转
- 提供用户认证（注册/登录/JWT）与户号绑定机制
- 提供用户首页仪表盘，展示待缴总额、用量趋势、报修状态等概览信息
- 代码仓库结构清晰，可一键初始化数据库与种子数据，可部署到 GitHub

## Non-Goals (Out of Scope)
- 不集成真实的第三方支付网关（支付宝/微信支付），仅提供模拟支付流程
- 不实现管理员后台（除了管理员种子账号外，不提供管理员专属 UI）
- 不实现短信/邮件通知推送
- 不实现多租户或多小区管理，仅面向单户用户场景
- 不实现移动端原生 APP，仅提供响应式 Web 端
- 不实现自动抄表或智能硬件对接，账单读数由种子数据或管理员录入

## Background & Context
- 项目采用前后端分离：后端 Flask (Python) 提供 REST API，前端 React + TypeScript + Vite + Tailwind CSS 提供交互界面。
- 数据库选用 MySQL 8.x，并提供 SQLite 作为本地开发备选（通过环境变量切换）。
- 当前项目目录已搭建基础骨架（数据模型、路由框架、前端页面结构），本 PRD 在现有骨架上规范功能边界，并指导后续的功能完善、测试与 GitHub 部署。

## Functional Requirements
- **FR-1 用户注册与登录**: 用户可以通过用户名+密码注册账号，登录后获取 JWT Token 访问受保护接口；支持获取当前登录用户信息。
- **FR-2 户号与表计管理**: 每个用户可绑定一户或多户户号，每户户号关联电/水/气三个表计（表号、当前读数等）。
- **FR-3 电费/水费/燃气费账单查询**: 用户可按费用类型筛选查看账单列表，包含计费周期、起止读数、用量、金额、缴费状态等；可查看某笔账单的阶梯计费拆分明细。
- **FR-4 在线模拟缴费**: 用户可对"待缴费"状态的账单发起支付，系统生成交易单号、更新账单状态为"已缴费"、记录表计当前读数、写入支付记录。
- **FR-5 分类缴费记录查询**: 支持按费用类型（全部/电/水/气）和缴费状态（全部/待缴/已缴）组合筛选，并在前端展示已缴/待缴金额汇总统计。
- **FR-6 计费规则可视化展示**: 分别展示电、水、气三类费用的阶梯计价规则（档位、用量区间、单价、说明），并提供典型用量场景下的费用计算示例。
- **FR-7 故障报修**: 用户可提交报修工单（报修类型：电/水/气/其他、故障描述、联系电话、紧急程度：普通/紧急），系统保存工单并提供工单列表与进度追踪（待处理→处理中→已解决）。
- **FR-8 仪表盘概览**: 用户登录后可看到首页概览：待缴总额、本月用量、已缴记录数、处理中报修数、近 6 月用量趋势图、快捷缴费入口、待缴账单预览。

## Non-Functional Requirements
- **NFR-1 性能**: 单次 API 响应时间 < 500ms（本地开发环境）；首屏加载 < 3s（构建后静态资源 + gzip）。
- **NFR-2 可用性与健壮性**: 后端提供统一错误响应（400/401/403/404/500），前端对接口错误有统一提示；关键数据库操作使用事务；密码使用加盐哈希存储（werkzeug security）。
- **NFR-3 安全**: JWT 无状态认证；CORS 开启凭据支持；SQL 注入防护通过 SQLAlchemy ORM 保障；XSS 通过 React 默认转义保障。
- **NFR-4 可维护性**: 前后端代码分层清晰（routes/services/models 与 pages/components/store）；配置通过环境变量注入；README 提供本地启动说明与 MySQL 初始化命令。
- **NFR-5 响应式 UI**: 桌面与移动端均可用（Tailwind grid + breakpoint）；移动端核心功能（缴费、报修、查看记录）操作流畅。

## Constraints
- **Technical**: 后端语言 Python 3.10+；Web 框架 Flask 3.x；ORM SQLAlchemy；认证 Flask-JWT-Extended；数据库 MySQL 8.x（或 SQLite 开发回退）；前端 React 18 + TypeScript + Vite + Tailwind CSS；状态管理 Zustand；HTTP 客户端 Axios；图表 Recharts。不得引入额外重量级框架。
- **Business**: 10 天交付周期；功能严格限定在 FR-1 至 FR-8。
- **Dependencies**: Python 依赖见 `backend/requirements.txt`；Node 依赖见 `package.json`。

## Assumptions
- 用户具备一台可运行 Python 3.10+ 与 Node 18+ 的开发机器。
- 本地或远程可访问 MySQL 实例（如无，可使用 SQLite 模式快速体验）。
- GitHub 仓库上传由用户通过本地 `git` 完成，或由本项目生成完整的 `.gitignore` 与项目结构供用户直接推送。
- 计费规则采用中国常见居民阶梯价格作为示例，可通过数据库表 `bill_type_rules` 灵活调整。

## Acceptance Criteria

### AC-1: 用户注册与登录
- **Given**: 数据库已初始化，且用户名未被占用
- **When**: 客户端提交 `POST /api/auth/register` 携带合法 username/password（≥6位）
- **Then**: 返回 201，包含 JWT token 与 user 对象；数据库写入 users 记录
- **Verification**: `programmatic`
- **Notes**: 登录 `POST /api/auth/login` 返回 200 + token；密码错误返回 401。

### AC-2: 户号与表计查询
- **Given**: 用户已登录（携带有效 JWT）
- **When**: 请求 `GET /api/households/mine`
- **Then**: 返回该用户绑定的所有户号及其下的电/水/气表计列表
- **Verification**: `programmatic`

### AC-3: 账单列表筛选
- **Given**: 用户已登录，且数据库存在多笔账单
- **When**: 请求 `GET /api/bills?type=electricity&status=unpaid&period=2026-05`
- **Then**: 仅返回同时满足类型、状态、周期筛选条件的账单；按 period 倒序
- **Verification**: `programmatic`

### AC-4: 账单详情含阶梯拆分
- **Given**: 用户已登录，存在指定 bill_id 的账单
- **When**: 请求 `GET /api/bills/{bill_id}`
- **Then**: 返回账单基本信息 + `breakdown` 阶梯明细数组 + 户号与表计信息 + 支付记录（如已付）
- **Verification**: `programmatic`

### AC-5: 模拟缴费成功
- **Given**: 用户已登录，账单状态为 unpaid
- **When**: 提交 `POST /api/bills/{bill_id}/pay`
- **Then**: 账单状态更新为 paid、写入 paid_at、写入 payments 记录、返回交易单号；重复支付返回 400
- **Verification**: `programmatic`

### AC-6: 缴费记录前端筛选
- **Given**: 前端已登录，进入「缴费记录」页面
- **When**: 用户点击类型筛选（电/水/气/全部）或状态筛选（待缴/已缴/全部）
- **Then**: 列表按筛选条件刷新，顶部已缴/待缴总额同步更新
- **Verification**: `human-judgment`

### AC-7: 计费规则页面展示
- **Given**: 前端未登录或已登录均可访问
- **When**: 访问「计费规则」页面
- **Then**: 三列卡片分别展示电/水/气阶梯价；下方展示三种典型场景的计算示例，合计金额与阶梯拆分正确
- **Verification**: `human-judgment`

### AC-8: 报修工单提交与列表
- **Given**: 用户已登录
- **When**: 提交 `POST /api/repairs` 携带合法类型/描述/电话/紧急程度
- **Then**: 返回 201，工单初始状态 pending；`GET /api/repairs` 可看到新工单并按时间倒序
- **Verification**: `programmatic`

### AC-9: 报修进度展示
- **Given**: 报修工单存在 pending/processing/resolved 三种状态
- **When**: 前端「故障报修」页面加载
- **Then**: 每张工单卡片显示状态标签与三步进度条（待处理→处理中→已解决），紧急工单显示"紧急"红标
- **Verification**: `human-judgment`

### AC-10: 仪表盘数据展示
- **Given**: 用户已登录，账单与报修数据完整
- **When**: 进入首页仪表盘
- **Then**: 四张统计卡片数值与 API `/api/dashboard` 返回一致；近 6 月用量趋势图表渲染正常；待缴账单列表最多展示 5 条
- **Verification**: `human-judgment`

### AC-11: 种子数据一键初始化
- **Given**: 配置好 MySQL 或 SQLite
- **When**: 执行 `cd backend && python seed.py`
- **Then**: 表结构创建完成，并写入 demo 与 admin 用户、1 户户号+3 个表计、完整阶梯规则、近 6 个月账单、3 条报修工单；控制台打印演示账号
- **Verification**: `programmatic`

### AC-12: 项目可构建与 GitHub 就绪
- **Given**: 依赖安装完成
- **When**: 执行 `npm install && npm run build` 和 `pip install -r backend/requirements.txt`
- **Then**: 前端产出 `dist/` 目录无 TypeScript 构建错误；后端无 import 错误；`.gitignore` 排除 `.env`、`__pycache__`、`node_modules`、`dist` 等
- **Verification**: `programmatic`

## Open Questions
- [ ] 是否需要管理员专属 UI（审核工单、录入读数、调整计费规则）？当前版本假设仅通过种子脚本 + 数据库操作实现。
- [ ] 是否需要导出缴费记录为 PDF/Excel？当前版本不包含。
- [ ] 是否需要支付前确认短信验证码？当前版本假设纯模拟支付。
