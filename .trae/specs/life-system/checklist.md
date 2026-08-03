# 生活缴费系统 - Verification Checklist

## 一、后端可运行性（对应 AC-1 / Task 1-2）
- [ ] 运行 `cd backend && pip install -r requirements.txt` 无报错且 exit code = 0
- [ ] 复制 `.env.example` 为 `.env` 并设置 `USE_SQLITE=true`
- [ ] 运行 `python seed.py` 输出 "✅ 种子数据写入完成"，成功生成 `backend/life_system.db`
- [ ] 运行 `python app.py`，Flask 服务监听 `0.0.0.0:5000`，控制台无异常
- [ ] `curl http://localhost:5000/api/health` 返回 `{"status":"ok","service":"life-system"}`

## 二、用户认证 API（AC-2 / Task 2）
- [ ] `POST /api/auth/register` 注册新用户返回 201，重复 username 返回 400
- [ ] `POST /api/auth/login` 使用 demo/demo123 返回 access_token（JWT 三段式）
- [ ] 带 `Authorization: Bearer <token>` 请求 `GET /api/auth/me` 返回 username=demo，role=user
- [ ] 不带 token 请求受保护接口（如 /api/bills）返回 401/422
- [ ] 使用 admin/admin123 登录，/api/auth/me 返回 role=admin

## 三、账单查询与筛选（AC-3 / Task 3）
- [ ] `GET /api/bills` 返回 demo 用户所有账单（seed 共 18 条），每条含 id/type/period/usage_amount/amount/status
- [ ] `GET /api/bills?type=electricity` 返回结果中 bill.type 全部为 electricity，共 6 条
- [ ] `GET /api/bills?type=water` 返回全部 water 类型；gas 同理
- [ ] `GET /api/bills?status=unpaid` 返回 period = 2026-04 与 2026-05 的 6 条账单
- [ ] `GET /api/bills?status=paid` 返回更早周期，无 unpaid 混入
- [ ] `GET /api/bills?type=electricity&status=unpaid` 组合筛选正确，仅 2 条（2026-04、2026-05 两期电费未缴）

## 四、账单详情与阶梯拆分（AC-4 / Task 3）
- [ ] `GET /api/bills/:id` 返回 bill 对象含 household、meter、breakdown 三个子结构
- [ ] breakdown 数组长度与该类型阶梯数一致（电 3 档、水 2 档、气 3 档或更少，视用量）
- [ ] breakdown 中每项 tier / min_usage / max_usage / unit_price / usage_in_tier / subtotal 字段均非空（除 max_usage 最高档可为 null）
- [ ] breakdown 各 subtotal 累加值 ≈ bill.amount（误差 ≤ 0.01）
- [ ] 对已支付账单，bill.payment 字段非空，含 transaction_no / method / paid_at

## 五、模拟支付流程（AC-5 / Task 3）
- [ ] `POST /api/bills/:unpaid_id/pay` 返回 payment_id、transaction_no、paid_at、bill
- [ ] transaction_no 以 "PAY" 开头，长度合理（20 字符左右）
- [ ] 支付完成后再次 GET /api/bills/:id，status = paid 且 paid_at 非空
- [ ] 对应 meter.current_reading 更新到账单 current_reading（不再是 seed 中的旧值）
- [ ] 对同一账单再次调用 pay 返回 400 + msg="该账单已支付"
- [ ] 对不存在的账单 id pay 返回 404；对他人账单 pay 返回 403

## 六、计费规则 API（AC-6 / Task 2）
- [ ] `GET /api/rules` 无需鉴权即可访问（返回 200 而非 401）
- [ ] 共 8 条规则：electricity 3 条（tier=1/2/3）+ water 2 条（tier=1/2）+ gas 3 条（tier=1/2/3）
- [ ] 电价 tier=1 单价 0.5880、tier=2 0.6380、tier=3 0.8880（与 seed 一致）
- [ ] 水价 tier=1 单价 3.5、tier=2 4.6；气价 tier=1 2.67、tier=2 2.95、tier=3 3.56
- [ ] `GET /api/rules?type=water` 只返回 2 条 water 规则；`?type=electricity` 返回 3 条

## 七、报修工单 API（AC-7 / Task 4）
- [ ] `POST /api/repairs` 缺 description 或 phone 返回 400 并提示
- [ ] 合法提交 type=gas + description + phone + urgency=urgent 返回 201 + repair 对象
- [ ] `GET /api/repairs` 返回列表包含新建工单，status=pending，urgency=urgent
- [ ] `GET /api/repairs/:id` 详情字段与创建入参一致（type/description/phone/urgency）
- [ ] 越权访问其他用户工单（或伪造不存在 id）返回 403 或 404
- [ ] seed 已有 3 条工单（1 resolved + 1 processing + 1 pending），列表共 4 条（含新建）

## 八、工作台 Dashboard API（AC-8 / Task 2）
- [ ] `GET /api/dashboard` 返回 unpaid_total、paid_total、this_month_usage、usage_chart、repairs
- [ ] unpaid_total = 所有 status=unpaid 账单 amount 之和（应为 2026-04 与 2026-05 共 6 条账单总额）
- [ ] paid_total = 所有 paid 账单 amount 之和
- [ ] this_month_usage 对象含 electricity / water / gas 三个数值（最近一期用量）
- [ ] usage_chart 为长度 6 的数组，每一项含 period + 三种用量，按时间升序
- [ ] repairs 对象含 pending / processing / resolved 三个计数（初始应为 1/1/1，新建后变为 2/1/1）

## 九、户号 API（FR-2）
- [ ] `GET /api/households/mine` 返回用户户号列表，含 household_no=HH20240001、address
- [ ] households.meters 关联电/水/气三块表计，meter_no 分别为 EL-0001 / WT-0001 / GS-0001

## 十、全局错误处理（FR-12）
- [ ] 请求不存在路径 `GET /api/nonexist` 返回 404 JSON: `{"msg":"资源不存在"}`
- [ ] 故意传错参数触发 400，返回 JSON 而非 HTML 错误页
- [ ] 所有错误响应 Content-Type: application/json

## 十一、前端依赖与类型检查（AC-9 / Task 5）
- [ ] `npm install` 成功，node_modules 目录生成，package-lock.json 未冲突
- [ ] `npm run check`（tsc --noEmit） exit code = 0，TS 无报错
- [ ] 检查 src/types.ts：Bill 类型含 breakdown 字段（可选数组）；RepairRequest 含 urgency/status

## 十二、前端生产构建（AC-9 / Task 6）
- [ ] `npm run build` 执行成功，dist/ 目录生成
- [ ] dist/index.html 存在且可解析，title 含「生活缴费系统」
- [ ] dist/assets/ 下有 JS bundle（*.js）与 CSS bundle（*.css），非空
- [ ] 构建过程无 webpack/vite 致命错误，无 ESLint 阻断级问题

## 十三、前端页面交互（AC-10 / Task 7）
- [ ] 登录页渲染：用户名/密码输入框 + 登录按钮 + 注册入口
- [ ] 登录成功跳转 /dashboard，侧边栏展示 5 个菜单项
- [ ] 工作台（Dashboard）：4 张统计卡 + 用量趋势柱图渲染无白屏
- [ ] 缴费中心（Payment）：电/水/气 3 个 Tab 可切换，待缴列表加载，点击缴费弹窗→确认→成功弹窗
- [ ] 支付成功后切回账单列表，该条账单不再出现（已移至已缴）
- [ ] 缴费记录（Records）：类型筛选 + 状态筛选交互即时生效；表格列完整
- [ ] 缴费记录详情抽屉：阶梯拆分卡片逐档展示，读数区/支付区信息正确
- [ ] 计费规则（Rules）：电/水/气三张阶梯卡片渲染，下方 3 个计算示例数字无误
- [ ] 故障报修（Repair）：表单 4 类类型按钮可选，提交后工单列表追加，进度条第一格高亮
- [ ] 全站浏览器 Console 无红色 Error（仅少量 Warning 可接受）

## 十四、代码规范与分层（NFR-4 / NFR-6）
- [ ] 后端路由层：routes/*.py 仅做参数解析 + 调用模型/服务，不直接写大段业务
- [ ] 后端计费逻辑独立于 services/billing.py，复用于 seed.py 与 API
- [ ] 前端 pages/ 页面组件 + components/ 通用组件 + store/ 状态管理分层清晰
- [ ] 无单文件超过 800 行（Payment.tsx 206 行、Records 234 行、Rules 172 行、Repair 248 行均达标）
- [ ] Python 端字符串统一使用双引号，docstring 以中文描述模块用途

## 十五、.gitignore 与敏感信息（AC-12 / Task 9）
- [ ] `.gitignore` 包含 `__pycache__/`、`*.pyc` 条目
- [ ] `.gitignore` 包含 `backend/.env`（避免密钥提交）
- [ ] `.gitignore` 包含 `backend/life_system.db`（SQLite 文件不入库）
- [ ] `.gitignore` 包含 `node_modules/` 与 `dist/`
- [ ] `.env.example` 含所有必需 env 变量的占位，SECRET_KEY 默认值已给出

## 十六、MySQL 脚本（AC-11 / FR-11）
- [ ] `backend/schema.sql` 包含 7 张 CREATE TABLE IF NOT EXISTS 语句（users/households/meters/bill_type_rules/bills/payments/repair_requests）
- [ ] 所有外键约束正确：users→households→meters→bills→payments；users→repair_requests
- [ ] 表字段类型与 models.py 定义一致（Enum、DECIMAL、VARCHAR 长度匹配）
- [ ] 脚本开头 `CREATE DATABASE IF NOT EXISTS life_system DEFAULT CHARSET utf8mb4`

## 十七、GitHub 推送（AC-12 / Task 9）
- [ ] `git remote -v` 显示 origin 指向用户 GitHub 仓库 HTTPS 或 SSH URL
- [ ] `git push origin main` 推送成功，远端显示新提交（或提示 "Everything up-to-date" 若未改）
- [ ] 用户在 GitHub 仓库网页浏览文件树：backend/、src/、public/、README.md、package.json、tsconfig.json、vite.config.ts、tailwind.config.js 均存在
- [ ] README.md 含功能特性、技术栈、两种启动方式（SQLite + MySQL）、演示账号表、API 接口表、阶梯计费示例
