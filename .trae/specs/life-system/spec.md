# 生活缴费系统 - Product Requirement Document

## Overview
- **Summary**: 面向社区居民的一站式公共事业缴费平台，提供电费、水费、燃气费的在线查询与缴纳、阶梯计费规则公开、缴费记录分类检索、以及故障报修工单管理。系统包含前后端分离架构，后端基于 Python Flask 提供 REST API，前端基于 React + TypeScript 提供现代化 Web UI，数据持久化采用 MySQL（同时提供 SQLite 作为开发体验回退方案）。
- **Purpose**: 解决居民线下排队缴费、查账困难、对计费标准不透明、报修流程繁琐等痛点，提供 7×24 小时线上自助服务入口，降低物业运营人力成本，同时提升居民生活便利性。
- **Target Users**: 社区住户（居民用户）、物业/系统管理员（预留 admin 角色）

## Goals
- 支持电费、水费、燃气费三种公共事业费用的在线缴纳，含支付确认与交易凭证生成
- 支持按费用类型（电/水/气）与缴费状态（待缴/已缴）组合筛选，查看缴费历史记录及账单阶梯拆分明细
- 公开展示电、水、气三类阶梯计费规则，附计算示例便于用户理解
- 支持用户提交故障报修工单（类型/描述/紧急程度/联系电话）并跟踪处理进度
- 提供工作台首页概览：待缴总额、本月用量统计、报修进度概览、近 6 月用量趋势图
- 支持用户注册、登录与 JWT 鉴权，确保用户数据隔离与接口安全
- 前后端可独立启动部署，最终代码上传至用户 GitHub 仓库

## Non-Goals (Out of Scope)
- 不接入真实支付网关（本项目为模拟支付，不产生真实扣款）
- 不实现抄表员移动端或上门抄表流程
- 不实现多户号绑定与家庭组共享（当前为 1 用户 → 1 户号 → 3 类表计的基础模型）
- 不实现物业派单、维修人员抢单等 B 端运维工作流（仅实现 C 端报修提交与进度查看）
- 不实现发票开具、费用报销等财务延伸功能
- 不提供短信/邮件通知推送

## Background & Context
- 工作区中已存在一份相对完整的前后端脚手架（Flask 后端 + React 前端），包含全部核心路由、数据模型、UI 页面与种子数据脚本。本项目任务为：验证该脚手架的完整性与正确性，修复潜在缺陷，最终确保可运行、可构建、可上传 GitHub。
- 技术栈由用户指定：后端 Python（Flask + SQLAlchemy + JWT），数据库 MySQL，前端不限（项目中已采用 React 18 + TypeScript + Vite + TailwindCSS + Zustand + Recharts）。
- 项目必须在 10 天内完成全链路验证与交付。

## Functional Requirements
- **FR-1 用户认证**: 支持用户名/密码注册与登录，基于 JWT 做接口鉴权，token 有效期 7 天；未登录用户访问受保护页面自动跳转登录
- **FR-2 户号与表计**: 用户开户后自动关联一个户号，户号下挂三块表计（电/水/气），用户可查看自己的户号信息
- **FR-3 账单生成与查询**: 系统存储户号历史账单（按周期 YYYY-MM），支持按 type（electricity/water/gas）、status（unpaid/paid）、period 过滤查询，返回账单列表
- **FR-4 账单详情**: 查看单个账单详情，包含读数区间、用量、金额、表计/户号信息；已支付账单附带交易凭证；并根据阶梯计费规则返回费用拆分明细（breakdown）
- **FR-5 账单支付**: 对待缴账单执行模拟支付，支付成功后标记账单为 paid，写入 payments 表，生成交易号，更新对应表计当前读数
- **FR-6 电费/水费/燃气费分类缴费**: 缴费中心页按 Tab 切换三种费用类型，各自展示对应待缴账单并完成支付
- **FR-7 缴费记录分类查看**: 缴费记录页支持「类型（全部/电/水/气）」与「状态（全部/待缴/已缴）」的组合筛选，支持点击账单查看详情抽屉
- **FR-8 计费规则展示**: 公开三种费用类型的阶梯档位（tier/min/max/单价/描述），附电费 250 度、水费 15 吨、燃气 45 立方的计算示例
- **FR-9 故障报修**: 用户可提交报修工单（类型电/水/气/其他 + 描述 + 电话 + 普通/紧急），工单状态流转 pending → processing → resolved，前端显示进度条
- **FR-10 工作台概览**: 首页展示已缴/待缴统计卡、本月用量统计卡、报修进度概览、近 6 月用量趋势柱状图
- **FR-11 种子数据**: 提供 seed.py 初始化脚本，一键建表并写入演示账号（demo/demo123、admin/admin123）、示例户号、阶梯规则、近 6 个月账单、3 条报修工单
- **FR-12 健康检查与错误处理**: 提供 /api/health 健康检查接口；全局 400/404/500 错误统一 JSON 返回

## Non-Functional Requirements
- **NFR-1 性能**: 单接口响应 < 500ms（本地 SQLite 环境、单用户前提下）；前端首屏加载 < 3s（dev server 冷启动 < 10s 可接受）
- **NFR-2 安全性**: 密码使用 werkzeug PBKDF2 哈希存储；所有业务接口（除 rules、auth、health 外）必须 JWT 鉴权；校验用户只能访问自己的户号、账单、工单
- **NFR-3 兼容性**: 后端支持 MySQL 8.0 与 SQLite 双模式（通过 USE_SQLITE env 切换）；前端支持 Chrome / Edge / Safari 现代浏览器
- **NFR-4 可维护性**: 前后端代码分层清晰（routes/models/services / components/pages/store/lib），无大文件超过 800 行
- **NFR-5 可部署性**: 后端 requirements.txt 可一键 pip 安装；前端 package.json 可一键 npm install 与 build；README 提供两种启动方式（SQLite 快速体验 / MySQL 生产）
- **NFR-6 代码规范**: Python 代码使用双引号字符串与中文 docstring；前端 TypeScript 类型完整、无 any 泄漏、tsc --noEmit 可通过

## Constraints
- **Technical**: 后端必须 Python（已用 Flask + Flask-SQLAlchemy + Flask-JWT-Extended）；数据库必须 MySQL（同时保留 SQLite fallback）；前端框架不限（项目已选 React 18 + TS + Vite）；不得更换为其他技术栈
- **Business**: 交付周期 10 个自然日；最终必须上传用户指定的 GitHub 仓库
- **Dependencies**: PyMySQL / cryptography / python-dotenv（后端）；axios / react-router / zustand / recharts / lucide-react / tailwindcss（前端）

## Assumptions
- 用户本地或目标服务器可安装 Python 3.9+ 与 Node.js 18+；若无 MySQL 环境，使用 SQLite fallback 即可体验
- 用户已持有 GitHub 账号并可提供仓库地址，或使用已配置好的 git remote origin 推送
- 阶梯计费规则参考国内常见居民计价标准（电价三档 0.588/0.638/0.888、水价二档 3.5/4.6、气价三档 2.67/2.95/3.56），实际部署可由管理员修改 seed 或直接改数据库
- 支付流程为模拟，无第三方支付 SDK 集成
- 当前环境已完成 git init 并存在 origin remote（git status 显示 "up to date with 'origin/main'"）

## Acceptance Criteria

### AC-1: 后端可启动并通过健康检查
- **Given**: 用户已执行 `cd backend && pip install -r requirements.txt && cp .env.example .env` 并将 USE_SQLITE 设为 true
- **When**: 运行 `python seed.py && python app.py`
- **Then**: Flask 服务在 http://localhost:5000 启动；GET /api/health 返回 `{"status":"ok","service":"life-system"}`；控制台无报错
- **Verification**: `programmatic`

### AC-2: 注册与登录接口可用
- **Given**: 后端已启动
- **When**: POST `/api/auth/register` 注册新用户，再 POST `/api/auth/login` 登录
- **Then**: 注册返回 201 与用户信息；登录返回 access_token（JWT）；使用该 token 请求 `/api/auth/me` 返回当前用户信息
- **Verification**: `programmatic`

### AC-3: 可查询账单列表并分类筛选
- **Given**: 使用 demo 账号登录并获取 token
- **When**: GET `/api/bills?type=electricity` 与 GET `/api/bills?status=unpaid`
- **Then**: 分别仅返回电费账单与未缴账单；列表含 id/type/period/usage_amount/amount/status 等字段
- **Verification**: `programmatic`

### AC-4: 账单详情返回阶梯拆分
- **Given**: 存在任意一条账单 id
- **When**: GET `/api/bills/:id`
- **Then**: 返回 bill 对象内含 breakdown 数组，每一项包含 tier / unit_price / usage_in_tier / subtotal；各阶梯 subtotal 累加值等于 bill.amount（误差 ±0.01）
- **Verification**: `programmatic`

### AC-5: 模拟支付成功并生成交易凭证
- **Given**: 存在一条 status=unpaid 的账单
- **When**: POST `/api/bills/:id/pay`
- **Then**: 返回 payment_id / transaction_no / paid_at；再次查询该账单 status=paid，paid_at 非空；meters.current_reading 更新至账单 current_reading
- **Verification**: `programmatic`

### AC-6: 计费规则接口返回三类阶梯
- **Given**: 后端已 seed
- **When**: GET `/api/rules`
- **Then**: 返回 electricity 3 条 + water 2 条 + gas 3 条，共 8 条规则；每条含 tier / min_usage / max_usage / unit_price
- **Verification**: `programmatic`

### AC-7: 报修工单可创建与查询
- **Given**: 已登录
- **When**: POST `/api/repairs` 创建工单（type=gas, description, phone, urgency=urgent），再 GET `/api/repairs`
- **Then**: 创建返回 201 与工单；列表包含该工单，type/description/urgency/status=pending 均与入参一致
- **Verification**: `programmatic`

### AC-8: 工作台接口返回概览数据
- **Given**: 已登录 demo 账号（存在近 6 月账单）
- **When**: GET `/api/dashboard`
- **Then**: 返回 unpaid_total / paid_total / this_month_usage（电水气分别）/ usage_chart（6 月数组）/ repairs 统计
- **Verification**: `programmatic`

### AC-9: 前端可构建成功
- **Given**: 根目录执行 `npm install` 完成
- **When**: 执行 `npm run build` 与 `npm run check`（tsc --noEmit）
- **Then**: 两个命令均 exit code 0；build 产物生成于 dist/ 目录
- **Verification**: `programmatic`

### AC-10: 前端核心页面可正常渲染
- **Given**: 前后端均已启动，访问 http://localhost:5173 并用 demo/demo123 登录
- **When**: 依次浏览「工作台 / 缴费中心 / 缴费记录 / 计费规则 / 故障报修」5 个页面
- **Then**: 页面无白屏、无控制台红色 error；各页面的 Tab 切换、筛选、弹窗交互均响应；缴费中心可完成一笔模拟支付并显示成功弹窗
- **Verification**: `human-judgment`

### AC-11: 数据库脚本可在 MySQL 执行
- **Given**: 用户安装 MySQL 8.0 并创建 life_system 库
- **When**: 在 MySQL 命令行执行 `source backend/schema.sql`，再运行后端 seed.py 使用 USE_SQLITE=false
- **Then**: 所有 7 张表创建成功无报错；seed 后 users/households/meters/bill_type_rules/bills/payments/repair_requests 均有数据
- **Verification**: `programmatic`

### AC-12: 代码已上传 GitHub
- **Given**: 项目 git 仓库已配置 remote origin
- **When**: 执行 `git push origin main`（或对应默认分支）
- **Then**: push 成功；用户在 GitHub 仓库网页可见全部前后端源码、README、.gitignore、配置文件等
- **Verification**: `human-judgment`

## Open Questions
- [ ] 用户的 GitHub 仓库具体 URL 是什么？当前已存在 origin remote，是否即为目标仓库？
- [ ] 是否需要额外补充单元测试 / e2e 测试脚本？当前 PRD 以手动 + curl 级 programmatic 验证为主
- [ ] 演示数据的周期是否需要贴近当前真实日期（当前 seed 写到 2026-05，env Today=2026-08-03，可能需要补 6/7/8 月账单）？
