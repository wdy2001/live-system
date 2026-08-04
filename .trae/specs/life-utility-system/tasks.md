# 生活缴费系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: 后端核心功能完善与 API 验证
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 验证并补全后端 6 个路由模块（auth / households / bills / rules / repairs / dashboard）的所有端点，确保符合 PRD AC-1 ~ AC-5, AC-8。
  - 重点检查：bills 筛选（type/status/period）、bills/:id 阶梯拆分（breakdown）、bills/:id/pay 幂等（paid 账单 400）、repairs 状态初始为 pending。
  - 若 `dashboard` 路由缺失则补全：返回 unpaid_total、unpaid_count、this_month_usage{electricity,water,gas}、repair_stats{pending,processing,resolved}、近 6 月 trends 列表。
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-8, AC-10, AC-11
- **Test Requirements**:
  - `programmatic` TR-1.1: 使用 SQLite 模式启动后端，`seed.py` 执行无报错，demo 用户可 login 返回 200 + token。
  - `programmatic` TR-1.2: 依次调用 `/api/bills?type=electricity&status=unpaid`、`/api/bills/{id}`、`/api/bills/{id}/pay`（后再调一次应 400），返回码与字段符合预期。
  - `programmatic` TR-1.3: 调用 `/api/repairs` POST 创建工单 → GET 列表包含新工单 → `/api/dashboard` 返回 repair_stats 正确。
  - `programmatic` TR-1.4: `/api/households/mine` 返回户号及 3 个 meters。
  - `human-judgement` TR-1.5: 代码 reviewer 检查 routes 与 services 分层，业务逻辑不在路由层堆砌；错误返回统一 JSON 格式 `{msg}`。
- **Notes**: 优先使用 SQLite 模式，避免本地 MySQL 阻塞测试。

## [x] Task 2: 前端 UI/UX 完善与前后端联调
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 验证并补全 6 个页面（Login / Register / Dashboard / Payment / Records / Rules / Repair）与核心组件（Layout、StatCard、UsageChart、TypeBadge、Skeleton）。
  - 确保 API 基础路径与 `/api` 前缀一致，axios 拦截器对 401 自动跳转登录，错误时 toast/alert 提示。
  - 响应式：手机宽度下 Payment 账单卡片正常换行，Records 表格切换为双列布局，Repair 表单单列。
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-9, AC-10, AC-12
- **Test Requirements**:
  - `programmatic` TR-2.1: `npm install && npm run check`（tsc --noEmit）通过，无类型错误；`npm run build` 成功生成 `dist/`。
  - `programmatic` TR-2.2: `npm run lint` 通过（可配置忽略）。
  - `human-judgement` TR-2.3: 人工走查主流程：Register → Login → Dashboard 数据加载 → Payment 选类型点缴费弹窗 → Records 筛选切 tab → Rules 三栏卡片 → Repair 提交工单看列表。
  - `human-judgement` TR-2.4: 移动端 375px 宽度下 UI 不溢出、按钮可点击；加载中显示骨架屏。
- **Notes**: 前端 dev server 通过 vite proxy 转发 `/api` 到后端 5000 端口；若无后端则使用 `USE_SQLITE=true` 启动后端联调。

## [x] Task 3: 数据库与种子数据完善
- **Priority**: medium
- **Depends On**: Task 1
- **Description**: 
  - 审核 `schema.sql` 与 `models.py` 一致性（字段、类型、索引、外键），补齐缺失索引（如 bills 上的 (household_id, type, period)）。
  - 审核 `seed.py`：确保近 6 个月账单按正确周期写入且 paid/unpaid 分界合理，阶梯规则 3+2+3=8 条完整，至少 3 条报修工单覆盖全部状态。
  - 确保 `schema.sql` 可独立在 MySQL 中执行成功（`USE life_system` 后逐表创建）。
- **Acceptance Criteria Addressed**: AC-11
- **Test Requirements**:
  - `programmatic` TR-3.1: `cd backend && USE_SQLITE=true python seed.py` 退出码 0 并打印账号信息。
  - `programmatic` TR-3.2: `mysql -u root < backend/schema.sql` （本地有 MySQL 时）执行成功无报错；表 users/households/meters/bill_type_rules/bills/payments/repair_requests 均存在。
  - `human-judgement` TR-3.3: reviewer 检查种子数据中 demo 用户的账单拆分金额与阶梯规则一致（例如电 100 度应为 0.588*100=58.8）。
- **Notes**: 无 MySQL 环境时以 SQLite 验证为主，schema.sql 语法审核为辅。

## [x] Task 4: 构建部署脚本与 GitHub 上传准备
- **Priority**: medium
- **Depends On**: Task 2, Task 3
- **Description**: 
  - 补全项目根 `README.md`：技术栈、10 天里程碑说明（Day1-3 后端 / Day4-6 前端 / Day7-8 数据 / Day9 部署 / Day10 验收）、本地启动三步曲（MySQL+seed / 后端启动 / 前端启动）、账号密码。
  - 完善 `.gitignore`：确保 `.env`、`.env.local`、`__pycache__/`、`*.pyc`、`*.sqlite3`、`node_modules/`、`dist/`、`.DS_Store` 被忽略。
  - 补充一键脚本（可选 shell）：`start-dev.sh` 同时启动前后端；或在 README 中明确两条命令即可。
- **Acceptance Criteria Addressed**: AC-12
- **Test Requirements**:
  - `programmatic` TR-4.1: 执行 `git status` 后 `node_modules/`、`dist/`、`backend/*.sqlite3`、`.env` 不出现为未追踪文件。
  - `human-judgement` TR-4.2: README 中快速开始步骤清晰可操作，复制即可完成本地启动（按 SQLite 模式）。
  - `human-judgement` TR-4.3: 目录结构一目了然，README 首屏给出功能模块与页面导航地图。
- **Notes**: 不写额外部署文档，仅 README。

## [x] Task 5: 整体功能验证与缺陷修复
- **Priority**: high
- **Depends On**: Task 1, Task 2, Task 3, Task 4
- **Description**: 
  - 全量冒烟测试：以 demo 账号走通全部 FR-1 ~ FR-8 场景，记录并修复遇到的所有 bug（如字段缺失、数字精度、路由 404、状态更新不刷新等）。
  - 修复任何 tsc 与 lint 告警中的硬错误。
- **Acceptance Criteria Addressed**: AC-1 ~ AC-12 全部
- **Test Requirements**:
  - `programmatic` TR-5.1: 后端健康检查 `/api/health` 返回 `{"status":"ok","service":"life-system"}`。
  - `programmatic` TR-5.2: 后端所有受保护接口无 token 时统一返回 401。
  - `human-judgement` TR-5.3: 人工执行 E2E 用例清单（checklist.md 中全部 checkpoints），逐项打勾，失败项立刻修复并复验。
  - `human-judgement` TR-5.4: 视觉与交互走查：颜色统一、按钮 hover 状态、弹窗可关闭、骨架屏与空状态合理。
- **Notes**: 此任务为交付前的最终关口，不通过则不得标记交付。
