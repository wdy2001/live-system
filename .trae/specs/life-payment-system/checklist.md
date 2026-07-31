# 生活缴费系统 - 验收检查清单

## 项目基础与脚手架
- [ ] Checkpoint 1.1: 根目录包含 backend/、frontend/ 与 README.md 三大部分
- [ ] Checkpoint 1.2: backend/requirements.txt 列出 FastAPI、Uvicorn、SQLAlchemy、PyMySQL、passlib[bcrypt]、python-jose[cryptography]、python-multipart、pytest 等依赖
- [ ] Checkpoint 1.3: frontend/package.json 包含 React 18、Vite、Ant Design、Axios、react-router-dom 依赖
- [ ] Checkpoint 1.4: 根目录存在 .gitignore，排除 __pycache__、venv、node_modules、dist、.env、*.log
- [ ] Checkpoint 1.5: 后端启动后 /health 返回 200，/docs 可访问 Swagger UI
- [ ] Checkpoint 1.6: 前端启动后 Vite 开发服务器默认首页可访问（端口 5173）

## 数据库与初始化
- [ ] Checkpoint 2.1: 执行 `python backend/init_db.py` 成功，无报错
- [ ] Checkpoint 2.2: MySQL 中存在 6 张表：users、billing_rules、meter_usages、payment_orders、bill_details、repair_orders
- [ ] Checkpoint 2.3: billing_rules 表至少覆盖电(electric)、水(water)、气(gas) 三类，每类至少 3 档阶梯数据
- [ ] Checkpoint 2.4: meter_usages 种子数据包含≥3 个示例户号（可按示例户号快速演示）
- [ ] Checkpoint 2.5: users 表 password 字段为 bcrypt 哈希（非明文）
- [ ] Checkpoint 2.6: payment_orders 表含 status 字段（unpaid/paid/overdue）、含 user_id、house_no、type、total_amount 字段
- [ ] Checkpoint 2.7: repair_orders 表含 status 字段（pending/processing/completed/cancelled）、含 urgency、type、address、user_id 字段

## 认证与鉴权
- [ ] Checkpoint 3.1: POST /api/auth/register 能成功注册唯一用户名，返回 user 信息（不含 password）
- [ ] Checkpoint 3.2: POST /api/auth/register 使用相同用户名返回 400/409 错误，提示已存在
- [ ] Checkpoint 3.3: POST /api/auth/login 使用正确凭证返回 access_token（JWT），token 24h 内有效
- [ ] Checkpoint 3.4: GET /api/users/me 携带有效 token 返回当前用户信息；不携带 token 返回 401
- [ ] Checkpoint 3.5: PUT /api/users/me 可修改姓名、手机号、地址等基本信息，读取后验证已更新
- [ ] Checkpoint 3.6: 伪造/过期 token 请求受保护接口返回 401

## 计费规则与金额计算
- [ ] Checkpoint 4.1: GET /api/billing-rules 返回电/水/气三类阶梯规则（可按 type 筛选），返回结构包含 tier_min/max、unit_price、extra_fee
- [ ] Checkpoint 4.2: 计算函数 calculate_bill(electric, 350 kwh) 金额与手工阶梯计算一致（误差≤0.01 元）
- [ ] Checkpoint 4.3: GET /api/meter-usage?house_no=X&type=electric&month=YYYY-MM 对首次访问户号会自动生成模拟用量并入库
- [ ] Checkpoint 4.4: 阶梯规则中的附加费（例如基金、污水处理费）在明细中单独列出、金额正确

## 缴费模块
- [ ] Checkpoint 5.1: POST /api/payments/query 按 house_no+type+month 返回应缴金额（total）与 bill 明细
- [ ] Checkpoint 5.2: 首次 query 会自动创建 status=unpaid 的 payment_order 与 bill_details
- [ ] Checkpoint 5.3: POST /api/payments/pay 传入 order_id 后，订单状态变为 paid，paid_at 记录时间戳
- [ ] Checkpoint 5.4: GET /api/payments/:id 仅本人可访问；他人访问返回 403；详情中含阶梯明细与附加费
- [ ] Checkpoint 5.5: 重复 pay 同一已缴订单返回明确错误（或幂等不报错但不重复修改）

## 缴费记录筛选与分页
- [ ] Checkpoint 6.1: GET /api/payments 默认返回当前用户全部订单（支持 page/page_size 分页）
- [ ] Checkpoint 6.2: type=electric 仅返回电费订单；type=water/gas 同理；status=paid 仅返回已缴费订单
- [ ] Checkpoint 6.3: start_date & end_date 基于 created_at 生效，边界日期正确
- [ ] Checkpoint 6.4: 返回体中 total 为总数，items 为当前页数据；分页越界返回空数组但不报错
- [ ] Checkpoint 6.5: 数据量足够时（12 条示例），page=2&page_size=5 返回 5 条，page=3 返回 2 条

## 故障报修模块
- [ ] Checkpoint 7.1: POST /api/repairs 创建工单后 status=pending，数据可在列表中查到
- [ ] Checkpoint 7.2: GET /api/repairs 仅返回当前登录用户的工单（跨用户不可见）
- [ ] Checkpoint 7.3: POST /api/repairs/:id/cancel 对 pending 工单 → cancelled；对 processing/completed 返回 400
- [ ] Checkpoint 7.4: GET /api/repairs/:id 返回详情，支持按 status 筛选（列表接口）
- [ ] Checkpoint 7.5: 报修单字段完整：type、urgency、address、contact_name、contact_phone、description、（可选 image_urls）

## 后端工程质量与测试
- [ ] Checkpoint 8.1: 后端路由按 APIRouter 拆分（auth/users/billing/payments/repairs），结构清晰
- [ ] Checkpoint 8.2: 统一异常处理返回 {code, message, data}，中文错误信息友好
- [ ] Checkpoint 8.3: CORS 已配置允许前端来源（localhost:5173），跨域请求无阻塞
- [ ] Checkpoint 8.4: `pytest backend/tests` 全部通过（覆盖率聚焦核心接口）
- [ ] Checkpoint 8.5: 关键 API 响应时间（/payments 列表、/payments/query）本地调试 < 500ms

## 前端基础与路由
- [ ] Checkpoint 9.1: 路由 /login、/register 未登录可访问；/、/pay、/records、/rules、/repair、/repair/list、/profile 未登录自动重定向到 /login
- [ ] Checkpoint 9.2: 登录后 Antd Layout 左侧菜单完整（首页/缴费/记录/计费规则/报修/我的），主题一致
- [ ] Checkpoint 9.3: axios 拦截器统一注入 Bearer Token；遇到 401 自动跳转登录并 toast 提示
- [ ] Checkpoint 9.4: 登录/注册表单校验：必填、手机号 11 位、密码长度≥6；错误提示清晰
- [ ] Checkpoint 9.5: 存在 404 兜底页

## 前端缴费与记录页
- [ ] Checkpoint 10.1: 缴费页步骤（选类型→输户号→查账单→确认→成功）完整串联，每步 UI 正常
- [ ] Checkpoint 10.2: 查询结果展示账单明细（阶梯、附加费、总金额），与后端返回一致
- [ ] Checkpoint 10.3: 缴费成功页展示订单号、金额、户号、缴费时间
- [ ] Checkpoint 10.4: 记录页筛选条件（类型/状态/日期范围）变更后正确触发查询，参数映射正确
- [ ] Checkpoint 10.5: 记录页表格分页正常（pageSize 可切换）；点击行/详情按钮展示 Modal/Drawer，含阶梯表格与汇总金额

## 前端计费规则与报修页
- [ ] Checkpoint 11.1: 计费规则页三个 Tab（电/水/气）切换正常，表格展示阶梯、单价、附加费说明，与后端 billing_rules 一致
- [ ] Checkpoint 11.2: 报修提交页表单字段齐全（报修类型/紧急程度/地址/联系人/手机/描述/图片占位），校验生效
- [ ] Checkpoint 11.3: 报修列表页四个状态 Tab（待受理/处理中/已完成/已取消）切换正常，点击详情 Drawer 展示全部字段
- [ ] Checkpoint 11.4: 仅"待受理"工单显示取消按钮；取消后状态 Tab 下该工单消失，"已取消"中出现
- [ ] Checkpoint 11.5: 我的页展示用户信息，修改后保存并显示保存成功提示；刷新后数据更新

## 端到端场景与交付
- [ ] Checkpoint 12.1: 主流程端到端 1：注册→登录→电费查询→缴费→记录页查到状态=已缴→点击看明细
- [ ] Checkpoint 12.2: 主流程端到端 2：水费/燃气费各走一遍，记录页按类型筛选正确
- [ ] Checkpoint 12.3: 主流程端到端 3：提交报修单→查看→取消工单；另提交一张通过种子/脚本模拟流转到 processing/completed 的演示工单
- [ ] Checkpoint 12.4: 主流程端到端 4：修改个人信息，再次进入"我的"查看生效
- [ ] Checkpoint 12.5: 计费规则页（未登录也可访问）Tab 切换与内容正常
- [ ] Checkpoint 12.6: 无控制台未捕获报错；交互流畅无明显卡顿

## GitHub 交付
- [ ] Checkpoint 13.1: Git 仓库已初始化，提交历史结构合理（feat/refactor/test 等语义）
- [ ] Checkpoint 13.2: git status 无不应提交的产物（node_modules、venv、__pycache__、dist、.env）
- [ ] Checkpoint 13.3: README.md 包含：项目简介、技术栈、目录结构、环境要求、MySQL 配置步骤（含示例 .env）、后端启动、前端启动、初始化脚本、常见问题
- [ ] Checkpoint 13.4: 本地按 README 克隆仓库 → 配置 → 初始化 → 启动 → 走主流程，可完整复现
- [ ] Checkpoint 13.5: 若用户提供了 GitHub 远程 URL 已成功推送；未提供时文档中附带明确的 `git remote add origin <URL> && git push -u origin main` 命令说明
