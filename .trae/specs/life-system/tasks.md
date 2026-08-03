# 生活缴费系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: 安装后端依赖并初始化数据库
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 执行 `cd backend && pip install -r requirements.txt` 安装 Flask、Flask-SQLAlchemy、Flask-JWT-Extended、PyMySQL、python-dotenv 等依赖
  - 复制 `.env.example` 为 `.env`，设置 `USE_SQLITE=true`（因当前环境无 MySQL，优先走 SQLite 回退路径）
  - 运行 `python seed.py` 建表并写入演示数据（demo/admin 用户、阶梯规则、近 6 月账单、报修工单）
  - 验证 seed 脚本无报错退出，确认 SQLite 数据库文件生成
- **Acceptance Criteria Addressed**: AC-1, AC-11
- **Test Requirements**:
  - `programmatic` TR-1.1: `pip install -r requirements.txt` exit code = 0
  - `programmatic` TR-1.2: `python seed.py` 输出 "✅ 种子数据写入完成" 且 exit code = 0
  - `programmatic` TR-1.3: `backend/life_system.db` 文件存在且非空（> 50KB）
- **Notes**: 若依赖安装失败（如 cryptography 编译），可尝试升级 pip 或使用预编译 wheel

## [x] Task 2: 启动 Flask 后端并验证健康检查与核心 API（含 paid_total 修复 + seed 周期更新）
- **Priority**: high
- **Depends On**: Task 1
- **Description**: 
  - 后台运行 `python app.py` 启动 Flask（端口 5000，host 0.0.0.0）
  - 使用 curl 验证 `/api/health` 返回 200 且 JSON 含 status=ok
  - 使用 curl 完成完整链路：register → login（拿 JWT）→ /api/auth/me → /api/households/mine → /api/dashboard → /api/rules
  - 验证各业务接口返回 200 且字段完整
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-6, AC-8
- **Test Requirements**:
  - `programmatic` TR-2.1: `curl -s http://localhost:5000/api/health | grep -q "ok"` 返回真
  - `programmatic` TR-2.2: `POST /api/auth/login` demo/demo123 能拿到 `access_token`
  - `programmatic` TR-2.3: 带 Bearer token 请求 `/api/auth/me` 返回 username=demo
  - `programmatic` TR-2.4: `GET /api/rules` 返回数组长度 = 8（电 3 + 水 2 + 气 3）
  - `programmatic` TR-2.5: `GET /api/dashboard` 返回 unpaid_total > 0 且 usage_chart 为长度 6 的数组
- **Notes**: 启动 Flask 用非阻塞模式（blocking=false），wait 2s 确保服务就绪

## [x] Task 3: 账单相关接口端到端验证（列表/筛选/详情/支付）
- **Priority**: high
- **Depends On**: Task 2
- **Description**: 
  - 以 demo 用户登录获取 token 后，验证 `GET /api/bills`、`/api/bills?type=electricity`、`/api/bills?status=unpaid` 三类筛选
  - 选 1 条 unpaid 账单，请求详情 `/api/bills/:id`，校验 breakdown 各阶梯累加值 = amount
  - 对该 unpaid 账单执行 `POST /api/bills/:id/pay`，校验 status 变为 paid、transaction_no 生成、表读数更新
  - 幂等性校验：再次支付同一条账单应返回 400 "已支付"
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: `/api/bills?type=water` 返回的所有 bill.type 均为 water
  - `programmatic` TR-3.2: `/api/bills?status=paid` 无 unpaid 条目
  - `programmatic` TR-3.3: 单条账单 breakdown[i].subtotal 之和与 bill.amount 差值 < 0.02
  - `programmatic` TR-3.4: 支付接口返回 transaction_no 前缀为 "PAY" 且长度合法
  - `programmatic` TR-3.5: 已支付账单再次调用 pay 接口返回 HTTP 400
- **Notes**: 注意 seed 中 2026-04 与 2026-05 为 unpaid（period >= "2026-04"），2025-12 至 2026-03 为 paid

## [x] Task 4: 报修工单接口创建与列表验证
- **Priority**: high
- **Depends On**: Task 2
- **Description**: 
  - 用 demo 账号提交 `POST /api/repairs`：type=gas、description="检测漏气"、phone="13800138000"、urgency=urgent
  - 再调用 `GET /api/repairs`，确认列表中包含新工单，status=pending，urgency=urgent
  - 调用 `GET /api/repairs/:id` 详情返回一致；尝试访问不属于自己的工单（用 admin token 或伪造 id）应返回 403
- **Acceptance Criteria Addressed**: AC-7, NFR-2
- **Test Requirements**:
  - `programmatic` TR-4.1: 报修创建接口返回 HTTP 201 且 repair.id > 0
  - `programmatic` TR-4.2: 列表包含该 id 且 urgency == "urgent"、status == "pending"
  - `programmatic` TR-4.3: 详情接口 /api/repairs/:id 字段与创建入参一致
  - `programmatic` TR-4.4: 越权访问他人工单返回 403 或 404
- **Notes**: 字段校验：空 description 应返回 400 "请填写故障描述"

## [x] Task 5: 安装前端依赖并运行 TypeScript 检查（已补充 Dashboard 类型字段）
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 根目录执行 `npm install` 安装 React 18、Vite、TypeScript、TailwindCSS、Zustand、Recharts 等依赖
  - 运行 `npm run check`（即 `tsc -b --noEmit`）校验 TS 类型正确性，确保无 any 泄漏、文件无未使用变量
  - 修复若有 TS 报错（如类型未导入、组件 props 不匹配）
- **Acceptance Criteria Addressed**: AC-9, NFR-6
- **Test Requirements**:
  - `programmatic` TR-5.1: `npm install` exit code = 0，node_modules 目录生成
  - `programmatic` TR-5.2: `npm run check` exit code = 0，TS 无 error 输出
  - `human-judgement` TR-5.3: 检查 src/types.ts 中 Bill / RepairRequest / User 类型与后端字段对齐
- **Notes**: 若 npm install 速度慢，可考虑 `npm install --registry=https://registry.npmmirror.com` 加速

## [x] Task 6: 构建前端生产版本并验证产物
- **Priority**: high
- **Depends On**: Task 5
- **Description**: 
  - 执行 `npm run build`（`tsc -b && vite build`）构建前端静态文件到 dist/ 目录
  - 检查 dist/ 目录内包含 index.html、assets/ 目录（CSS + JS bundle）、favicon 引用
  - 验证 dist/index.html 可被 Flask `send_from_directory("../dist", "index.html")` 正确引用（路径存在）
- **Acceptance Criteria Addressed**: AC-9, NFR-5
- **Test Requirements**:
  - `programmatic` TR-6.1: `npm run build` exit code = 0，无 fatal error
  - `programmatic` TR-6.2: `dist/index.html` 文件存在且大小 > 1KB
  - `programmatic` TR-6.3: `dist/assets/` 目录下至少有 1 个 .js 与 1 个 .css 文件
- **Notes**: Vite 默认输出到 dist/，与 app.py 里的 send_from_directory 参数保持一致

## [ ] Task 7: 启动前端 dev server 并验证核心页面渲染（人类检查或浏览器自动化）
- **Priority**: medium
- **Depends On**: Task 2, Task 5
- **Description**: 
  - 运行 `npm run dev` 启动 Vite dev server（端口 5173）
  - 使用浏览器自动化或人工浏览：
    1. 打开登录页 → 用 demo/demo123 登录 → 跳转工作台
    2. 工作台：统计卡数值 > 0、用量图表能渲染、无白屏
    3. 缴费中心：切换 电/水/气 Tab，待缴列表渲染，点「立即缴费」弹窗 → 确认支付 → 成功弹窗
    4. 缴费记录：切换类型/状态筛选，点击「详情」打开抽屉，阶梯拆分卡片展示
    5. 计费规则：三类阶梯卡片渲染、计算示例 3 个都展示
    6. 故障报修：提交表单成功后列表多一条 pending 工单，进度条第一格高亮
- **Acceptance Criteria Addressed**: AC-10
- **Test Requirements**:
  - `human-judgement` TR-7.1: 登录成功后路由跳转到 /dashboard，页面显示"工作台"标题
  - `human-judgement` TR-7.2: 缴费中心支付流程完整走通，成功弹窗出现后 records 页对应账单为已缴
  - `human-judgement` TR-7.3: 缴费记录筛选交互不卡死，详情抽屉内容完整
  - `human-judgement` TR-7.4: 报修提交后列表即时刷新，新工单显示"紧急"标签
  - `programmatic` TR-7.5: Vite dev server 启动无 fatal，5173 端口监听
- **Notes**: 若无法使用浏览器，至少确保 dev server 启动成功且 vite 控制台无错误即可

## [ ] Task 8: 修正种子数据账单周期贴近当前日期（可选优化）
- **Priority**: low
- **Depends On**: Task 1
- **Description**: 
  - 当前日期为 2026-08-03，但 seed.py 中账单仅写到 2026-05，相差 3 个月
  - 可选：在 seed.py 中按当前年月动态生成近 6 个月的周期（例如 2026-03 至 2026-08），并使最近 1–2 期为 unpaid
  - 重新 seed 后 dashboard 本月用量更贴近真实场景
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `programmatic` TR-8.1: 若实施此修改，seed 后最大 period 应等于 `YYYY-MM` 格式的当前或上一个月
  - `human-judgement` TR-8.2: 工作台近 6 月柱状图显示最新月份在最右
- **Notes**: 此任务为低优先级优化，不阻塞主流程；如 seed 已有 6 月数据可不做

## [ ] Task 9: 检查 Git 仓库配置并推送到 GitHub
- **Priority**: high
- **Depends On**: Task 3, Task 4, Task 6
- **Description**: 
  - 运行 `git remote -v` 查看当前 origin 地址，确认 URL 为用户 GitHub 仓库
  - 检查 `.gitignore` 是否包含：`__pycache__/`、`*.pyc`、`backend/.env`、`backend/life_system.db`、`node_modules/`、`dist/`、`.DS_Store`
  - 如有新变更（如 seed 修正、bug fix、.trae 目录等）执行 `git add -A && git commit -m "feat: complete life system verification & spec docs"`
  - 执行 `git push origin main` 推送代码
  - 如 push 失败（无权限、remote 不存在），记录错误提示并提供解决方案
- **Acceptance Criteria Addressed**: AC-12
- **Test Requirements**:
  - `programmatic` TR-9.1: `.gitignore` 文件包含 backend/.env / node_modules / dist 条目
  - `programmatic` TR-9.2: `git status` 显示工作树干净（或已 commit 所有变更）
  - `human-judgement` TR-9.3: `git push origin main` 执行成功，GitHub 仓库网页刷新可见新提交
  - `human-judgement` TR-9.4: 仓库文件树包含 backend/、src/、public/、README.md、package.json、requirements.txt 等核心文件
- **Notes**: 若当前环境未配置 GitHub 凭据，push 可能需要用户手动介入；可提供远端地址让用户在本地完成推送
