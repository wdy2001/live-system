# 生活缴费系统 - 实施计划（10天开发周期）

## [ ] Task 1: 项目初始化与数据库设计（Day 1）
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 创建项目根目录结构（backend/, frontend/）
  - 后端项目初始化：FastAPI + SQLAlchemy + MySQL 连接配置
  - 前端项目初始化：Vue 3 + Element Plus + Vue Router + Pinia
  - 数据库表结构设计与建表脚本：
    - users（用户表）
    - electric_meters / water_meters / gas_meters（户号表）
    - electric_bills / water_bills / gas_bills（账单表）
    - payment_records（缴费记录表）
    - billing_rules（计费规则表）
    - repair_orders（故障报修表）
  - 编写数据库初始化脚本和种子数据
- **Acceptance Criteria Addressed**: NFR-4, NFR-5, NFR-6
- **Test Requirements**:
  - `programmatic` TR-1.1: 后端项目可正常启动，连接 MySQL 成功
  - `programmatic` TR-1.2: 前端项目可正常启动，首页可访问
  - `programmatic` TR-1.3: 所有数据库表创建成功，种子数据正确插入
  - `human-judgment` TR-1.4: 项目目录结构清晰，代码组织合理
- **Notes**: 使用 Alembic 或直接 SQL 脚本均可，优先保证开发效率

## [ ] Task 2: 用户认证模块 - 后端（Day 1-2）
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - 实现用户注册 API（POST /api/auth/register）
  - 实现用户登录 API（POST /api/auth/login），返回 JWT Token
  - 实现用户信息获取 API（GET /api/auth/me）
  - 密码使用 bcrypt 加密存储
  - JWT 认证中间件，受保护路由需携带有效 Token
  - Pydantic 数据模型定义（请求/响应 Schema）
- **Acceptance Criteria Addressed**: AC-1, AC-2, NFR-3
- **Test Requirements**:
  - `programmatic` TR-2.1: 注册接口可创建新用户，密码为密文存储
  - `programmatic` TR-2.2: 登录接口验证正确凭证返回 JWT，错误凭证返回 401
  - `programmatic` TR-2.3: 受保护接口无 Token 返回 401，带有效 Token 返回正常数据
  - `programmatic` TR-2.4: 重复用户名注册返回错误提示
- **Notes**: Token 有效期设置为 24 小时

## [ ] Task 3: 用户认证模块 - 前端（Day 2）
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 登录页面：用户名/密码输入、登录按钮、注册跳转链接
  - 注册页面：用户名/密码/确认密码/手机号输入、注册按钮、登录跳转
  - 前端路由守卫：未登录用户自动跳转登录页
  - Token 本地存储（localStorage）与请求拦截器自动携带
  - 用户状态管理（Pinia store）
  - 登出功能
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 注册表单提交成功后跳转登录页
  - `programmatic` TR-3.2: 登录成功后 Token 存入 localStorage，跳转首页
  - `programmatic` TR-3.3: 未登录访问受保护页面自动跳转登录页
  - `human-judgment` TR-3.4: 登录/注册页面布局美观，表单验证提示友好
- **Notes**: 使用 Element Plus 表单组件，包含前端表单验证

## [ ] Task 4: 户号管理模块 - 后端（Day 3）
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 电表户号 CRUD API（增删改查，关联用户）
  - 水表户号 CRUD API
  - 燃气表户号 CRUD API
  - 每个类型户号列表查询接口
  - 设置默认户号接口
- **Acceptance Criteria Addressed**: AC-15
- **Test Requirements**:
  - `programmatic` TR-4.1: 可添加新户号，归属正确用户
  - `programmatic` TR-4.2: 可查询当前用户所有户号列表
  - `programmatic` TR-4.3: 可删除户号，不可删除其他用户的户号
  - `programmatic` TR-4.4: 可设置默认户号
- **Notes**: 每户号添加时自动生成一条模拟当月账单

## [ ] Task 5: 电费缴费模块 - 后端（Day 3）
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - 电费账单查询 API（按户号查询当前账单）
  - 电费缴费 API（模拟支付，更新账单状态，生成缴费记录）
  - 历史电费账单列表查询
  - 账单数据模型：户号、用电量、应缴金额、已缴金额、账单周期、状态
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-5.1: 查询当前户号电费账单返回正确数据
  - `programmatic` TR-5.2: 缴费成功后账单已缴金额增加，状态更新
  - `programmatic` TR-5.3: 缴费成功后 payment_records 表生成对应记录
  - `programmatic` TR-5.4: 缴费金额为 0 或负数返回错误
- **Notes**: 模拟支付直接成功，不调用第三方支付

## [ ] Task 6: 水费缴费模块 - 后端（Day 4）
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - 水费账单查询 API（按户号查询当前账单）
  - 水费缴费 API（模拟支付，更新账单状态，生成缴费记录）
  - 历史水费账单列表查询
  - 账单数据模型：户号、用水量、应缴金额、已缴金额、账单周期、状态
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-6.1: 查询当前户号水费账单返回正确数据
  - `programmatic` TR-6.2: 缴费成功后账单已缴金额增加，状态更新
  - `programmatic` TR-6.3: 缴费成功后 payment_records 表生成对应记录
  - `programmatic` TR-6.4: 缴费金额为 0 或负数返回错误
- **Notes**: 代码结构参考电费模块，保持一致性

## [ ] Task 7: 燃气缴费模块 - 后端（Day 4）
- **Priority**: high
- **Depends On**: Task 4
- **Description**:
  - 燃气费账单查询 API（按户号查询当前账单）
  - 燃气费缴费 API（模拟支付，更新账单状态，生成缴费记录）
  - 历史燃气费账单列表查询
  - 账单数据模型：户号、用气量、应缴金额、已缴金额、账单周期、状态
- **Acceptance Criteria Addressed**: AC-7, AC-8
- **Test Requirements**:
  - `programmatic` TR-7.1: 查询当前户号燃气账单返回正确数据
  - `programmatic` TR-7.2: 缴费成功后账单已缴金额增加，状态更新
  - `programmatic` TR-7.3: 缴费成功后 payment_records 表生成对应记录
  - `programmatic` TR-7.4: 缴费金额为 0 或负数返回错误
- **Notes**: 代码结构参考电费模块，保持一致性

## [ ] Task 8: 前端布局与导航（Day 5）
- **Priority**: high
- **Depends On**: Task 3
- **Description**:
  - 整体布局：左侧导航栏 + 顶部栏 + 主内容区
  - 侧边栏导航菜单：首页、电费缴费、水费缴费、燃气缴费、缴费记录、计费规则、故障报修、户号管理
  - 顶部栏：用户信息展示、登出按钮
  - 首页仪表盘：快捷入口卡片、欠费提醒、最近缴费记录概览
  - 响应式布局适配
- **Acceptance Criteria Addressed**: AC-16, NFR-2
- **Test Requirements**:
  - `programmatic` TR-8.1: 所有导航菜单项可正常跳转
  - `programmatic` TR-8.2: 登录后显示主布局，登出后回到登录页
  - `human-judgment` TR-8.3: 整体布局美观，配色协调，导航清晰
  - `human-judgment` TR-8.4: 响应式布局在不同屏幕尺寸下显示正常
- **Notes**: 使用 Element Plus Layout 组件，风格简洁现代

## [ ] Task 9: 缴费功能前端页面（Day 5-6）
- **Priority**: high
- **Depends On**: Task 5, Task 6, Task 7, Task 8
- **Description**:
  - 电费缴费页面：户号选择下拉、账单信息展示、缴费金额输入、确认缴费按钮、缴费结果弹窗
  - 水费缴费页面：同上结构，水费数据
  - 燃气缴费页面：同上结构，燃气数据
  - 户号管理弹窗/页面：添加/删除户号，设置默认户号
  - API 接口封装（axios 请求封装）
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-15
- **Test Requirements**:
  - `programmatic` TR-9.1: 电费页面加载后显示当前户号账单信息
  - `programmatic` TR-9.2: 输入金额点击缴费，成功后账单状态实时更新
  - `programmatic` TR-9.3: 可切换不同户号查看对应账单
  - `programmatic` TR-9.4: 户号管理可添加、删除、设置默认户号
  - `human-judgment` TR-9.5: 缴费流程交互顺畅，反馈及时
- **Notes**: 三个缴费页面结构相似，可抽取公共组件

## [ ] Task 10: 缴费记录模块 - 后端（Day 6）
- **Priority**: high
- **Depends On**: Task 5, Task 6, Task 7
- **Description**:
  - 缴费记录列表查询 API，支持分页
  - 按缴费类型筛选（electric/water/gas/all）
  - 按时间范围筛选（开始日期、结束日期）
  - 按缴费状态筛选（success/failed/pending）
  - 缴费记录详情查询 API
- **Acceptance Criteria Addressed**: AC-9, AC-10
- **Test Requirements**:
  - `programmatic` TR-10.1: 无筛选条件时返回当前用户所有缴费记录
  - `programmatic` TR-10.2: 按类型筛选只返回对应类型记录
  - `programmatic` TR-10.3: 按时间范围筛选只返回区间内记录
  - `programmatic` TR-10.4: 分页参数生效，返回正确的总数和当前页数据
- **Notes**: payment_records 表统一存储所有类型缴费记录，用 type 字段区分

## [ ] Task 11: 缴费记录模块 - 前端（Day 7）
- **Priority**: high
- **Depends On**: Task 10, Task 8
- **Description**:
  - 缴费记录列表页面：筛选表单（类型、时间范围、状态）、数据表格、分页
  - 记录详情弹窗：展示缴费完整信息
  - 空状态展示
- **Acceptance Criteria Addressed**: AC-9, AC-10
- **Test Requirements**:
  - `programmatic` TR-11.1: 页面加载显示缴费记录列表
  - `programmatic` TR-11.2: 选择筛选条件点击查询，列表数据正确过滤
  - `programmatic` TR-11.3: 点击详情按钮弹出详情弹窗，信息完整
  - `human-judgment` TR-11.4: 列表布局清晰，筛选操作便捷
- **Notes**: 使用 Element Plus Table + Pagination 组件

## [ ] Task 12: 计费规则模块（Day 7）
- **Priority**: medium
- **Depends On**: Task 8
- **Description**:
  - 后端：计费规则数据初始化（电费阶梯电价、水费阶梯水价、燃气阶梯气价）
  - 后端：计费规则查询 API（按类型查询）
  - 前端：计费规则页面，分 Tab 展示电费/水费/燃气费规则
  - 规则内容：阶梯档次、单价、说明文字
- **Acceptance Criteria Addressed**: AC-11
- **Test Requirements**:
  - `programmatic` TR-12.1: 计费规则 API 返回正确的规则数据
  - `programmatic` TR-12.2: 前端页面分类型展示规则内容
  - `human-judgment` TR-12.3: 规则展示清晰易懂，排版美观
- **Notes**: 规则数据可存储在数据库或配置文件中，优先数据库

## [ ] Task 13: 故障报修模块 - 后端（Day 8）
- **Priority**: high
- **Depends On**: Task 2
- **Description**:
  - 提交报修申请 API（POST /api/repair）
  - 报修记录列表查询 API（当前用户）
  - 报修详情查询 API
  - 报修状态流转模拟（待处理 -> 处理中 -> 已完成）
  - 数据模型：报修类型、问题描述、地址、联系人、联系电话、状态、处理备注、创建时间
- **Acceptance Criteria Addressed**: AC-12, AC-13, AC-14
- **Test Requirements**:
  - `programmatic` TR-13.1: 提交报修成功，状态为"待处理"
  - `programmatic` TR-13.2: 报修列表返回当前用户所有报修记录
  - `programmatic` TR-13.3: 报修详情包含完整信息和处理进度
  - `programmatic` TR-13.4: 只能查看自己的报修记录，不能查看他人的
- **Notes**: 可加一个模拟处理进度的后台定时任务或手动触发接口

## [ ] Task 14: 故障报修模块 - 前端（Day 8-9）
- **Priority**: high
- **Depends On**: Task 13, Task 8
- **Description**:
  - 故障报修提交页面：表单（故障类型选择、问题描述、地址、联系人、电话）、提交按钮
  - 报修记录列表页面：列表展示、状态标签、详情按钮
  - 报修详情弹窗/页面：完整信息展示、处理进度时间线
- **Acceptance Criteria Addressed**: AC-12, AC-13, AC-14
- **Test Requirements**:
  - `programmatic` TR-14.1: 填写报修单提交成功，列表显示新报修
  - `programmatic` TR-14.2: 报修列表显示所有报修记录及状态
  - `programmatic` TR-14.3: 点击详情查看完整报修信息
  - `human-judgment` TR-14.4: 表单交互友好，状态展示清晰
- **Notes**: 状态使用不同颜色标签区分

## [ ] Task 15: 联调测试与 Bug 修复（Day 9）
- **Priority**: high
- **Depends On**: Task 9, Task 11, Task 12, Task 14
- **Description**:
  - 全流程端到端测试：注册 -> 登录 -> 添加户号 -> 缴费 -> 查看记录 -> 报修
  - 前端错误处理完善（网络错误、后端错误提示）
  - 加载状态、空状态、异常状态处理
  - 边界条件测试（金额超限、重复提交等）
  - 修复发现的 Bug
- **Acceptance Criteria Addressed**: 所有 AC
- **Test Requirements**:
  - `programmatic` TR-15.1: 完整业务流程可走通，无阻断性 Bug
  - `programmatic` TR-15.2: 错误场景有友好提示，不白屏
  - `programmatic` TR-15.3: 重复提交、金额异常等边界情况处理正确
  - `human-judgment` TR-15.4: 整体使用流畅，用户体验良好
- **Notes**: 重点测试数据一致性和异常处理

## [ ] Task 16: 项目完善与 GitHub 上传（Day 10）
- **Priority**: high
- **Depends On**: Task 15
- **Description**:
  - 编写项目 README.md（项目介绍、技术栈、启动步骤、目录结构）
  - 后端 requirements.txt 依赖整理
  - 前端 package.json 依赖确认
  - 编写数据库初始化 SQL 脚本
  - 配置 .env.example 环境变量示例
  - 初始化 Git 仓库，提交代码
  - 创建 GitHub 远程仓库并推送
  - 最终验证和文档完善
- **Acceptance Criteria Addressed**: NFR-6
- **Test Requirements**:
  - `programmatic` TR-16.1: README 清晰说明启动步骤，新人可按文档启动项目
  - `programmatic` TR-16.2: 代码已成功推送到 GitHub 远程仓库
  - `programmatic` TR-16.3: 项目依赖完整，重新安装可正常运行
  - `human-judgment` TR-16.4: 代码注释清晰，目录结构规范
- **Notes**: Git 提交记录规范，使用语义化提交信息
