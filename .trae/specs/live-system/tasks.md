# 生活缴费系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 项目初始化与数据库设计
- **Priority**: high
- **Depends On**: None
- **Description**: 
  - 初始化后端项目结构（FastAPI + SQLAlchemy + MySQL）
  - 初始化前端项目结构（React + TypeScript + Vite）
  - 设计并创建数据库表结构（用户、账单、缴费记录、报修工单、计费规则、账户余额）
  - 配置 docker-compose 开发环境
- **Acceptance Criteria Addressed**: [NFR-4]
- **Test Requirements**:
  - `programmatic` TR-1.1: 数据库表创建成功，包含 users, bills, payment_records, repair_orders, pricing_rules, wallets, wallet_transactions 表
  - `programmatic` TR-1.2: docker-compose up 可成功启动 MySQL 服务
  - `human-judgement` TR-1.3: 项目目录结构清晰，前后端分离合理
- **Notes**: 数据库表需考虑外键关系和索引优化

## [ ] Task 2: 用户认证系统（后端）
- **Priority**: high
- **Depends On**: [Task 1]
- **Description**: 
  - 实现用户注册 API（用户名、密码、户号）
  - 实现用户登录 API，返回 JWT Token
  - 实现 JWT 认证中间件
  - 密码使用 bcrypt 加密存储
- **Acceptance Criteria Addressed**: [AC-1, NFR-2]
- **Test Requirements**:
  - `programmatic` TR-2.1: POST /api/auth/register 成功创建用户，密码已加密
  - `programmatic` TR-2.2: POST /api/auth/login 正确凭证返回 200 和 JWT Token
  - `programmatic` TR-2.3: 错误密码登录返回 401
  - `programmatic` TR-2.4: 受保护接口无 Token 返回 401
- **Notes**: Token 有效期 24 小时

## [ ] Task 3: 账户余额管理（后端）
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**: 
  - 实现余额查询 API
  - 实现账户充值 API
  - 实现充值记录查询 API
  - 创建钱包和交易记录表
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-3.1: GET /api/wallet/balance 返回当前用户余额
  - `programmatic` TR-3.2: POST /api/wallet/recharge 成功增加余额并生成交易记录
  - `programmatic` TR-3.3: GET /api/wallet/transactions 返回充值记录列表
- **Notes**: 充值为模拟充值，无需真实支付

## [ ] Task 4: 账单与缴费模块（后端）
- **Priority**: high
- **Depends On**: [Task 3]
- **Description**: 
  - 实现账单查询 API（按类型：电费/水费/燃气费）
  - 实现账单缴费 API（从余额扣款）
  - 实现缴费记录查询 API（支持按类型筛选）
  - 生成模拟账单数据
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-4, AC-5]
- **Test Requirements**:
  - `programmatic` TR-4.1: GET /api/bills?type=electricity 返回电费账单列表
  - `programmatic` TR-4.2: POST /api/bills/{id}/pay 余额充足时缴费成功，余额不足返回错误
  - `programmatic` TR-4.3: 缴费后账单状态变为 paid，生成对应缴费记录
  - `programmatic` TR-4.4: GET /api/payments?type=water 返回水费缴费记录
- **Notes**: 账单类型：electricity, water, gas

## [ ] Task 5: 计费规则模块（后端）
- **Priority**: medium
- **Depends On**: [Task 1]
- **Description**: 
  - 实现计费规则查询 API
  - 初始化电费、水费、燃气费的阶梯计费规则数据
  - 计费规则包含：基础价格、阶梯价格、计算说明
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-5.1: GET /api/pricing 返回所有类型的计费规则
  - `programmatic` TR-5.2: GET /api/pricing/{type} 返回指定类型的计费规则详情
- **Notes**: 计费规则为静态配置数据

## [ ] Task 6: 故障报修模块（后端）
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**: 
  - 实现报修工单创建 API
  - 实现报修工单列表查询 API
  - 实现报修工单详情 API
  - 工单状态：待处理、处理中、已完成
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-6.1: POST /api/repairs 创建报修工单成功
  - `programmatic` TR-6.2: GET /api/repairs 返回当前用户的报修列表
  - `programmatic` TR-6.3: GET /api/repairs/{id} 返回工单详情
  - `programmatic` TR-6.4: 工单初始状态为 pending
- **Notes**: 报修类型：electrical, plumbing, gas

## [ ] Task 7: 用户认证与全局布局（前端）
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**: 
  - 实现登录页面
  - 实现注册页面
  - 实现全局导航栏和布局
  - 集成路由和状态管理（React Router + Context）
  - 封装 API 请求层（axios 拦截器）
- **Acceptance Criteria Addressed**: [AC-1, NFR-5]
- **Test Requirements**:
  - `programmatic` TR-7.1: 登录页面可正常访问，表单验证有效
  - `programmatic` TR-7.2: 登录成功后跳转首页，Token 存储在 localStorage
  - `human-judgement` TR-7.3: 页面布局美观，导航清晰
- **Notes**: 使用 Ant Design 或类似 UI 组件库

## [ ] Task 8: 首页与账户模块（前端）
- **Priority**: medium
- **Depends On**: [Task 7, Task 3]
- **Description**: 
  - 实现系统首页（展示余额、待缴账单数量等概览信息）
  - 实现账户余额展示
  - 实现账户充值功能页面
  - 实现充值记录列表
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-8.1: 首页展示用户余额和待缴账单统计
  - `programmatic` TR-8.2: 充值功能可正常使用，余额实时更新
  - `human-judgement` TR-8.3: 页面交互流畅，状态反馈及时
- **Notes**: 首页为登录后的默认页面

## [ ] Task 9: 账单缴费模块（前端）
- **Priority**: high
- **Depends On**: [Task 7, Task 4]
- **Description**: 
  - 实现电费账单列表与缴费页面
  - 实现水费账单列表与缴费页面
  - 实现燃气费账单列表与缴费页面
  - 实现缴费记录页面（支持按类型筛选）
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-4, AC-5]
- **Test Requirements**:
  - `programmatic` TR-9.1: 各费用类型账单列表页面可正常加载数据
  - `programmatic` TR-9.2: 点击缴费按钮可完成缴费操作
  - `programmatic` TR-9.3: 缴费记录页面支持按类型筛选
  - `human-judgement` TR-9.4: 账单信息展示清晰，缴费流程顺畅
- **Notes**: 三个缴费页面结构相似，可复用组件

## [ ] Task 10: 计费规则页面（前端）
- **Priority**: medium
- **Depends On**: [Task 7, Task 5]
- **Description**: 
  - 实现计费规则展示页面
  - 分 Tab 展示电费、水费、燃气费计费规则
  - 清晰展示阶梯价格和计算说明
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-10.1: 计费规则页面可正常加载数据
  - `human-judgement` TR-10.2: 计费规则展示清晰易懂，格式美观
- **Notes**: 重点在信息展示的清晰度

## [ ] Task 11: 故障报修模块（前端）
- **Priority**: high
- **Depends On**: [Task 7, Task 6]
- **Description**: 
  - 实现报修表单提交页面
  - 实现报修记录列表页面
  - 实现报修工单详情页面
  - 工单状态可视化展示
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-11.1: 报修表单可正常提交
  - `programmatic` TR-11.2: 报修记录列表可正常加载
  - `programmatic` TR-11.3: 工单详情页面展示完整信息
  - `human-judgement` TR-11.4: 状态展示直观，表单验证友好
- **Notes**: 报修类型下拉选择，描述为必填项

## [ ] Task 12: 部署文档与 GitHub 上传
- **Priority**: medium
- **Depends On**: [Task 1-11]
- **Description**: 
  - 编写项目 README 文档
  - 编写 docker-compose 部署配置
  - 编写数据库初始化脚本
  - 整理代码并提交至 GitHub
- **Acceptance Criteria Addressed**: [AC-9, NFR-4]
- **Test Requirements**:
  - `programmatic` TR-12.1: docker-compose up 可一键启动完整系统
  - `human-judgement` TR-12.2: README 文档完整，包含部署说明和功能介绍
  - `human-judgement` TR-12.3: GitHub 仓库结构清晰，代码规范
- **Notes**: 包含 .gitignore，排除 node_modules 和环境变量文件
