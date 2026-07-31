# 生活缴费系统 - 实施计划（10天交付）

## [x] Task 1: 项目脚手架与仓库初始化
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 创建后端（FastAPI）与前端（React+Vite）项目目录结构
  - 初始化 Git 仓库与 .gitignore
  - 编写 README（启动步骤、MySQL 配置说明）
  - 提供后端 requirements.txt 与前端 package.json 基础依赖
- **Acceptance Criteria Addressed**: AC-7, AC-8
- **Test Requirements**:
  - `programmatic` TR-1.1: 后端 `uvicorn main:app --reload` 启动后访问 `/health` 返回 200
  - `programmatic` TR-1.2: 前端 `npm run dev` 启动后 Vite 默认首页可访问（端口 5173）
  - `human-judgement` TR-1.3: README 步骤清晰，复制命令即可完成依赖安装与启动
- **Notes**: /workspace 下创建 backend/、frontend/、README.md 根目录三部分

## [x] Task 2: MySQL 数据库设计与初始化脚本
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 设计 6 张核心表：users、billing_rules、meter_usages、payment_orders、repair_orders、bill_details（详见 ER 关系：users 1:N payment_orders 1:1 bill_details；billing_rules N:1 公用类型；meter_usages 按月生成；repair_orders 归属用户）
  - 编写 SQLAlchemy ORM 模型（models.py）
  - 编写 alembic 或原生 SQL 建表脚本 + 种子数据（计费规则、示例户号月度用量）
  - 编写 `init_db.py` 初始化脚本，执行后一次性建表并灌种子数据
- **Acceptance Criteria Addressed**: AC-2, AC-4, AC-7
- **Test Requirements**:
  - `programmatic` TR-2.1: 执行 `python backend/init_db.py` 后 SHOW TABLES 列出 6 张表
  - `programmatic` TR-2.2: billing_rules 表包含电/水/气三类阶梯数据，meter_usages 至少包含 3 个示例户号的当月用量
  - `human-judgement` TR-2.3: 表结构注释清晰、字段命名一致（snake_case）、有主键与必要索引（user_id、order_no、house_no、type、month）
- **Notes**: billing_rules 包含字段：id, type(electric/water/gas), tier_min, tier_max, unit_price, extra_fee_name, extra_fee_rate, description；payment_orders 包含 status(unpaid/paid/overdue)

## [x] Task 3: 后端认证模块（注册/登录/JWT）
- **Priority**: high
- **Depends On**: Task 2
- **Description**: 
  - 实现 `/api/auth/register` POST：校验用户名唯一、手机号、密码使用 bcrypt 哈希入库，返回用户信息
  - 实现 `/api/auth/login` POST：用户名密码校验，签发 JWT（HS256，24h 过期，payload 含 sub=user_id）
  - 实现 FastAPI Depends `get_current_user` 依赖：验证 Authorization: Bearer <token>，返回 ORM User 对象；缺失/过期/篡改返回 401
  - 实现 `/api/users/me` GET/PUT：查看与修改当前用户基本信息
- **Acceptance Criteria Addressed**: AC-1, AC-6
- **Test Requirements**:
  - `programmatic` TR-3.1: pytest 用例覆盖 register→login→me 流程
  - `programmatic` TR-3.2: 请求 `/api/users/me` 不带 Token 或带错误 Token 返回 401
  - `programmatic` TR-3.3: 数据库 users.password 字段不以明文出现，长度符合 bcrypt 规范
- **Notes**: 依赖：passlib[bcrypt], python-jose[cryptography], python-multipart

## [x] Task 4: 后端计费规则与计量查询模块
- **Priority**: high
- **Depends On**: Task 2
- **Description**: 
  - 公开接口 `/api/billing-rules` GET：按 type 查询阶梯计费规则（可不登录访问）
  - 内部工具函数 `calculate_bill(type, usage_kwh_or_m3)`：依据 billing_rules 阶梯计算基础费 + 附加费，返回明细 {tier_items: [{min,max,usage,price}], base_total, extra_fee, total}
  - `/api/meter-usage` GET（需登录）：按 house_no + type + month 查询当月用量数据；若不存在则按照户号生成模拟数据并入库（FR-10）
- **Acceptance Criteria Addressed**: AC-4, AC-2
- **Test Requirements**:
  - `programmatic` TR-4.1: `/api/billing-rules?type=electric` 返回阶梯规则（3 档单价）与附加费
  - `programmatic` TR-4.2: calculate_bill(electric, 350 kwh) 根据阶梯计算的结果与人工计算一致（误差 <0.01）
  - `programmatic` TR-4.3: 查询不存在的 meter_usage 后表中自动插入一条模拟记录
- **Notes**: 电费示例阶梯：0-180 度 0.52 元；181-280 度 0.57 元；281+ 度 0.87 元 + 0.05 元/度基金附加

## [x] Task 5: 后端缴费订单模块（查询待缴 + 模拟缴费）
- **Priority**: high
- **Depends On**: Task 3, Task 4
- **Description**: 
  - `/api/payments/query` POST（需登录）：参数 house_no + type + month → 查 meter_usage → 调用 calculate_bill → 返回待缴金额与明细；若未生成订单则同时创建 status=unpaid 的 payment_order +  bill_details
  - `/api/payments/pay` POST（需登录）：参数 order_id → 将订单 status 改为 paid + paid_at=now，模拟支付成功；返回缴费成功结果
  - `/api/payments/:id` GET（需登录）：查看订单详情（含 bill_details 明细）
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-5.1: 调用 query 后返回 total 金额；再调用 pay 后订单状态变为 paid
  - `programmatic` TR-5.2: 非订单创建者（other user）无法访问他人订单详情（403）
  - `human-judgement` TR-5.3: bill_details 包含阶梯各档用量与单价、附加费名称与金额

## [x] Task 6: 后端缴费记录分类筛选模块
- **Priority**: medium
- **Depends On**: Task 5
- **Description**: 
  - `/api/payments` GET（需登录）：列表查询，支持查询参数 type（electric/water/gas/all）、status（unpaid/paid/overdue/all）、start_date、end_date、page、page_size
  - 返回总条数 total、当前页数据 items；item 字段含订单号、户号、类型、月份、总金额、状态、创建/缴费时间
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-6.1: 生成多类型订单后，按 type=electric 筛选仅返回电费订单
  - `programmatic` TR-6.2: 分页参数 page=2&page_size=5 返回对应条数（假设存在 12 条时，第 2 页为 5 条，第 3 页 2 条）
  - `programmatic` TR-6.3: start_date / end_date 筛选基于 created_at 字段生效
- **Notes**: 对 created_at、user_id 建组合索引保证查询效率

## [x] Task 7: 后端故障报修模块
- **Priority**: medium
- **Depends On**: Task 3
- **Description**: 
  - `/api/repairs` POST（需登录）：创建报修单，字段 type（e.g., electric_leak/water_leak/gas_leak/other→映射到电/水/气大类）、address、contact_name、contact_phone、urgency(low/middle/high)、description、image_urls（可选列表）
  - `/api/repairs` GET（需登录）：列表查询当前用户的报修单，支持按 status(pending/processing/completed/cancelled) 筛选
  - `/api/repairs/:id` GET：查看详情（含处理进度时间线）
  - `/api/repairs/:id/cancel` POST：仅 status=pending 的工单可被创建者取消 → 改为 cancelled
  - 种子脚本或 debug 接口模拟：pending→processing→completed 的状态流转（便于前端演示）
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-7.1: 创建后状态=pending；cancel 后变为 cancelled；processing/completed 工单 cancel 返回 400
  - `programmatic` TR-7.2: 列表接口仅返回当前登录用户的工单（跨用户隔离）
  - `human-judgement` TR-7.3: 图片字段作为数组存储，结构清晰便于前端展示

## [x] Task 8: 后端联调、中间件与测试
- **Priority**: high
- **Depends On**: Task 3 ~ Task 7
- **Description**: 
  - 统一异常处理（返回结构化 JSON {code, message, data}）
  - CORS 中间件配置（允许 http://localhost:5173 等前端来源）
  - 路由聚合（APIRouter 按 auth/users/billing/payments/repairs 拆分）
  - 写 pytest 套件：核心接口覆盖，执行 `pytest backend/tests` 全量通过
  - 新增 `/health` 与 `/api/docs`（Swagger UI）访问检查
- **Acceptance Criteria Addressed**: AC-1 ~ AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-8.1: `pytest backend/tests` 通过率 100%
  - `programmatic` TR-8.2: `/docs` 可访问并列出全部接口
  - `human-judgement` TR-8.3: 错误响应统一、有意义；中文错误信息友好

## [x] Task 9: 前端页面开发（路由/布局/认证 + 缴费/记录 + 规则/报修）

## [x] Task 10: 前端缴费与记录页面（已包含在上一项合并完成）

## [x] Task 11: 前端计费规则与报修页面（已包含在上一项合并完成）

## [x] Task 12: 全链路联调补充、README 完善、测试修正

## [x] Task 13: GitHub 仓库准备与推送（本地 Git 初始化完成）
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 使用 React Router 配置路由：/login, /register, /, /pay, /records, /rules, /repair, /repair/list, /profile
  - 使用 Ant Design Layout（Sider + Header + Content），菜单包含首页、缴费、记录、计费规则、报修、我的
  - 编写 axios 拦截器：自动注入 Bearer Token、401 跳登录页、统一 error message toast
  - 编写登录页与注册页表单（用户名、密码、手机号、验证码占位）
  - 编写 404 与 403 提示页
- **Acceptance Criteria Addressed**: AC-1, AC-7
- **Test Requirements**:
  - `programmatic` TR-9.1: 未登录状态访问受保护路由被重定向至 /login
  - `human-judgement` TR-9.2: 登录后布局左侧菜单完整、颜色主题一致
  - `human-judgement` TR-9.3: 表单校验（必填、手机号格式、密码长度≥6）生效

## [ ] Task 10: 前端缴费与记录页面
- **Priority**: high
- **Depends On**: Task 9
- **Description**: 
  - 缴费页 /pay：步骤表单（选择类型→输入户号→查询并展示账单明细→确认支付→成功页），调用 payments/query 与 payments/pay
  - 记录页 /records：筛选条件（类型、状态、日期范围）、分页列表、点击行查看账单明细 Modal（阶梯、附加费、订单号、户号、月份、金额、时间）
- **Acceptance Criteria Addressed**: AC-2, AC-3
- **Test Requirements**:
  - `human-judgement` TR-10.1: 查询-缴费-成功三步流程顺畅、成功页展示订单号与总金额
  - `programmatic` TR-10.2: 记录页筛选与分页参数正确映射到后端查询参数
  - `human-judgement` TR-10.3: 明细 Modal 中阶梯表格与金额汇总与后端返回一致

## [ ] Task 11: 前端计费规则与报修页面
- **Priority**: medium
- **Depends On**: Task 9
- **Description**: 
  - 计费规则页 /rules：三个 Tab（电/水/气），阶梯表格 + 附加费说明，调用 billing-rules 接口
  - 报修提交页 /repair：表单（报修类型、紧急程度、地址、联系人、手机、描述、图片上传占位），调用 repairs POST
  - 报修列表页 /repair/list：按状态 Tab（待受理/处理中/已完成/已取消）、查看详情 Drawer、待受理可取消按钮
  - 我的页 /profile：展示并修改用户基本信息（PUT /users/me）
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `human-judgement` TR-11.1: 计费规则 Tab 切换显示对应阶梯，数据与 API 返回一致
  - `programmatic` TR-11.2: 报修提交成功后列表页第一条为新工单、状态=待受理
  - `human-judgement` TR-11.3: 取消按钮仅在待受理工单中可见；点击后状态切换成功

## [ ] Task 12: 全链路联调、E2E 场景与性能检查
- **Priority**: medium
- **Depends On**: Task 8, Task 10, Task 11
- **Description**: 
  - 端到端场景走查：注册→登录→查电费→缴费→看记录；查看规则；提交报修单→取消；修改个人资料
  - 修复联调中发现的字段映射/分页/筛选/日期格式等问题
  - 后端响应时间基础检查（/payments 列表响应 < 500ms）
  - README 补充完整初始化与联调步骤
- **Acceptance Criteria Addressed**: AC-1 ~ AC-7
- **Test Requirements**:
  - `programmatic` TR-12.1: 后端 pytest 全通过
  - `programmatic` TR-12.2: 手动端到端脚本化（可选 Cypress/Playwright 简单覆盖登录缴费主流程）
  - `human-judgement` TR-12.3: 主流程零错误，体验流畅

## [ ] Task 13: GitHub 仓库准备与推送
- **Priority**: high
- **Depends On**: Task 12
- **Description**: 
  - 完善 .gitignore（排除 __pycache__、venv、node_modules、dist、.env、*.log）
  - 准备根目录 README：项目简介、技术栈、目录结构、环境要求、MySQL 配置示例、一键启动步骤、常见问题
  - 准备提交规范的 Git 提交记录
  - 在本地完成 git add/commit；若用户提供了远程仓库地址则推送；未提供则给出 `git remote add origin <URL> && git push -u origin main` 清晰指导
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `human-judgement` TR-13.1: 仓库目录结构清晰，README 可复现
  - `human-judgement` TR-13.2: 克隆后按 README 可成功启动并通过 AC-1~AC-6 手动验证
  - `programmatic` TR-13.3: git status 无 node_modules/ 等不应提交的文件
