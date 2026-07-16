# 生活缴费系统 - 实施计划（分解与优先级任务列表）

## [ ] Task 1: 项目初始化与数据库设计
- **Priority**: high
- **Depends On**: None
- **Description**:
  - 创建项目目录结构（backend/、frontend/）
  - 后端使用 Flask + SQLAlchemy + Flask-JWT-Extended
  - 前端使用 Vue 3 + Vite + Element Plus
  - 设计 MySQL 数据库表结构（用户表、户号表、账单表、缴费记录表、计费规则表、故障报修表）
  - 编写数据库初始化脚本和种子数据
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8]
- **Test Requirements**:
  - `programmatic` TR-1.1: 数据库表创建成功，包含所有必要字段和索引
  - `programmatic` TR-1.2: 种子数据插入成功（计费规则、示例户号、示例账单）
  - `programmatic` TR-1.3: 后端项目可正常启动，数据库连接正常
  - `programmatic` TR-1.4: 前端项目可正常启动，首页可访问
- **Notes**: 使用 Flask 作为后端框架，SQLAlchemy 作为 ORM，数据库迁移使用 Flask-Migrate

## [ ] Task 2: 用户认证模块（注册/登录/鉴权）
- **Priority**: high
- **Depends On**: [Task 1]
- **Description**:
  - 实现用户注册接口（用户名、密码、手机号）
  - 实现用户登录接口，返回 JWT token
  - 实现用户登出功能
  - 实现 JWT 鉴权中间件
  - 前端实现登录/注册页面
  - 前端实现路由守卫和 token 管理
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-2.1: 注册接口返回成功，密码加密存储在数据库
  - `programmatic` TR-2.2: 登录接口返回 JWT token，验证正确的用户名密码
  - `programmatic` TR-2.3: 受保护接口在无 token 时返回 401，有有效 token 时正常访问
  - `programmatic` TR-2.4: 前端登录页面可正常提交，登录成功后跳转首页
  - `human-judgement` TR-2.5: 登录/注册页面 UI 美观，表单验证友好
- **Notes**: 使用 Werkzeug 进行密码哈希，Flask-JWT-Extended 处理 token

## [ ] Task 3: 用户中心与户号绑定
- **Priority**: high
- **Depends On**: [Task 2]
- **Description**:
  - 实现获取/更新用户信息接口
  - 实现户号绑定/解绑接口（电费、水费、燃气费户号）
  - 实现用户余额查询（模拟余额）
  - 前端实现个人中心页面
  - 前端实现户号管理功能
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-3.1: 用户信息查询和更新接口正常工作
  - `programmatic` TR-3.2: 户号绑定/解绑接口正常，关联关系正确存储
  - `programmatic` TR-3.3: 个人中心页面显示用户信息和已绑定户号
  - `programmatic` TR-3.4: 绑定户号时验证户号是否存在
- **Notes**: 户号预存在系统中，用户通过输入户号进行绑定

## [ ] Task 4: 计费规则模块
- **Priority**: medium
- **Depends On**: [Task 1]
- **Description**:
  - 实现计费规则查询接口（电费、水费、燃气费阶梯价格）
  - 前端实现计费规则展示页面
  - 展示阶梯电价、阶梯水价、阶梯气价的详细规则
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-4.1: 计费规则接口返回正确的阶梯价格数据
  - `programmatic` TR-4.2: 前端计费规则页面展示完整的三类费用规则
  - `human-judgement` TR-4.3: 计费规则展示清晰易懂，表格/卡片布局合理
- **Notes**: 计费规则为系统预置数据，包含各阶梯的用量区间和单价

## [ ] Task 5: 账单查询与缴费模块（电/水/燃气）
- **Priority**: high
- **Depends On**: [Task 3]
- **Description**:
  - 实现账单查询接口（按户号和费用类型）
  - 实现缴费接口（模拟支付，更新账单状态，生成缴费记录）
  - 前端实现电费缴费页面
  - 前端实现水费缴费页面
  - 前端实现燃气费缴费页面
  - 模拟缴费确认流程
- **Acceptance Criteria Addressed**: [AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-5.1: 账单查询接口返回对应用户绑定户号的待缴账单
  - `programmatic` TR-5.2: 缴费接口成功后账单状态更新为已缴，生成缴费记录
  - `programmatic` TR-5.3: 电费缴费页面可正常查看账单和完成缴费
  - `programmatic` TR-5.4: 水费缴费页面可正常查看账单和完成缴费
  - `programmatic` TR-5.5: 燃气费缴费页面可正常查看账单和完成缴费
  - `human-judgement` TR-5.6: 缴费流程顺畅，提示信息清晰
- **Notes**: 缴费为模拟流程，点击确认缴费即完成，不涉及真实支付

## [ ] Task 6: 缴费记录查询模块
- **Priority**: high
- **Depends On**: [Task 5]
- **Description**:
  - 实现缴费记录列表接口（支持按类型筛选、分页）
  - 实现缴费记录详情接口
  - 前端实现缴费记录列表页面
  - 实现类型筛选功能（全部/电费/水费/燃气费）
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-6.1: 缴费记录接口返回当前用户的缴费记录列表
  - `programmatic` TR-6.2: 按类型筛选正确返回对应类型的记录
  - `programmatic` TR-6.3: 前端列表页展示记录的时间、金额、类型、状态
  - `programmatic` TR-6.4: 筛选功能正常工作，切换类型时列表更新
- **Notes**: 列表按时间倒序排列，支持分页

## [ ] Task 7: 故障报修模块
- **Priority**: medium
- **Depends On**: [Task 2]
- **Description**:
  - 实现故障报修提交接口（类型、描述、地址、联系方式）
  - 实现报修记录查询接口（列表和详情）
  - 前端实现故障报修提交页面
  - 前端实现报修记录列表页面
  - 工单状态：待处理、处理中、已完成
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-7.1: 报修提交接口成功创建工单，状态为待处理
  - `programmatic` TR-7.2: 报修记录接口返回当前用户的报修列表
  - `programmatic` TR-7.3: 前端报修表单可正常提交
  - `programmatic` TR-7.4: 前端报修记录列表展示工单状态和详情
  - `human-judgement` TR-7.5: 报修表单字段清晰，状态展示直观
- **Notes**: 工单状态由系统模拟更新，初始为待处理

## [ ] Task 8: 前端整体优化与导航
- **Priority**: medium
- **Depends On**: [Task 4, Task 5, Task 6, Task 7]
- **Description**:
  - 实现顶部导航栏和侧边栏菜单
  - 实现首页仪表盘（展示待缴账单、最近缴费记录概览）
  - 统一页面布局和样式风格
  - 增加加载状态和错误提示
  - 响应式布局适配
- **Acceptance Criteria Addressed**: [AC-9]
- **Test Requirements**:
  - `programmatic` TR-8.1: 导航菜单可正常跳转各功能页面
  - `programmatic` TR-8.2: 首页展示待缴账单数量和最近缴费记录
  - `human-judgement` TR-8.3: 整体 UI 风格统一美观，交互流畅
  - `human-judgement` TR-8.4: 加载状态和错误提示友好
- **Notes**: 使用 Element Plus 组件库保持风格统一

## [ ] Task 9: GitHub 仓库初始化与项目文档
- **Priority**: low
- **Depends On**: [Task 1]
- **Description**:
  - 初始化 Git 仓库
  - 编写 .gitignore 文件
  - 编写项目 README 文档（功能介绍、技术栈、部署说明）
  - 编写后端启动说明
  - 编写前端启动说明
  - 推送到 GitHub 仓库
- **Acceptance Criteria Addressed**: [AC-9]
- **Test Requirements**:
  - `programmatic` TR-9.1: Git 仓库初始化成功，.gitignore 配置正确
  - `programmatic` TR-9.2: README 文档包含项目介绍、技术栈、快速开始指南
  - `programmatic` TR-9.3: 代码成功推送到 GitHub 远程仓库
  - `human-judgement` TR-9.4: 文档清晰完整，新用户可按文档启动项目
- **Notes**: README 需包含环境要求、安装步骤、配置说明

## [ ] Task 10: 整体测试与修复
- **Priority**: high
- **Depends On**: [Task 8, Task 9]
- **Description**:
  - 端到端功能测试
  - 修复发现的 bug
  - 代码优化和清理
  - 最终验证
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9]
- **Test Requirements**:
  - `programmatic` TR-10.1: 所有核心功能流程正常运行无报错
  - `programmatic` TR-10.2: 数据库数据一致性正确
  - `programmatic` TR-10.3: 前后端接口联调全部通过
  - `human-judgement` TR-10.4: 整体体验流畅，无明显 UI 问题
- **Notes**: 进行全流程回归测试
