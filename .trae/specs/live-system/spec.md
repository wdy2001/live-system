# 生活缴费系统 - Product Requirement Document

## Overview
- **Summary**: 一个面向居民用户的生活缴费管理系统，提供电费、水费、燃气费在线缴费服务，支持缴费记录查询、计费规则查看以及故障报修功能。系统采用前后端分离架构，后端使用 Python + FastAPI，前端使用 React + TypeScript，数据库采用 MySQL。
- **Purpose**: 解决居民日常缴纳生活费用不便、查询记录分散、报修流程繁琐的问题，提供一站式生活服务平台。
- **Target Users**: 城市居民用户、物业管理人员

## Goals
- 实现电费、水费、燃气费的在线缴费功能
- 支持按类别查看历史缴费记录
- 提供清晰透明的计费规则说明
- 支持用户提交故障报修申请并跟踪进度
- 系统代码托管至 GitHub

## Non-Goals (Out of Scope)
- 不实现真实支付渠道对接（使用模拟支付）
- 不实现管理员后台（仅面向普通用户）
- 不实现消息推送功能
- 不实现多租户/多小区管理
- 不实现发票开具功能

## Background & Context
- 项目周期为 10 天，需在有限时间内交付核心功能
- 采用前后端分离架构，便于独立开发和部署
- 使用 MySQL 作为关系型数据库，保证数据一致性
- 代码需上传至 GitHub 进行版本管理

## Functional Requirements
- **FR-1**: 用户注册与登录，支持基于 JWT 的身份认证
- **FR-2**: 电费缴费：用户可查询电费账单并完成缴费
- **FR-3**: 水费缴费：用户可查询水费账单并完成缴费
- **FR-4**: 燃气费缴费：用户可查询燃气费账单并完成缴费
- **FR-5**: 缴费记录查询：用户可按费用类型分类查看历史缴费记录
- **FR-6**: 计费规则展示：用户可查看各费用类型的计费标准说明
- **FR-7**: 故障报修：用户可提交故障报修申请，查看报修进度和历史记录
- **FR-8**: 用户账户余额管理：支持充值和余额查询

## Non-Functional Requirements
- **NFR-1**: 系统响应时间：页面加载 < 2s，API 响应 < 500ms
- **NFR-2**: 数据安全：密码使用 bcrypt 加密存储，敏感操作需鉴权
- **NFR-3**: 代码质量：后端代码覆盖率 > 70%，前后端均有基本错误处理
- **NFR-4**: 可部署性：提供 docker-compose 一键部署方案
- **NFR-5**: 兼容性：支持主流现代浏览器（Chrome、Firefox、Safari）

## Constraints
- **Technical**: 后端 Python + FastAPI，数据库 MySQL，前端框架选用 React + TypeScript
- **Business**: 10 天开发周期，核心功能优先
- **Dependencies**: MySQL 8.0+，Python 3.9+，Node.js 18+

## Assumptions
- 用户账号与房屋/户号一一绑定，注册时录入户号
- 账单数据由系统模拟生成，不接入真实公用事业系统
- 支付流程为模拟支付，直接从账户余额扣款
- 故障报修由系统内置状态流转，无人工审核流程

## Acceptance Criteria

### AC-1: 用户注册登录
- **Given**: 用户访问系统
- **When**: 用户填写注册信息（用户名、密码、户号）并提交
- **Then**: 系统创建用户账户，用户可使用账号密码登录并获得 JWT Token
- **Verification**: `programmatic`
- **Notes**: 密码需加密存储，Token 有效期 24 小时

### AC-2: 电费缴费
- **Given**: 用户已登录，存在待缴电费账单
- **When**: 用户进入电费页面，查看账单并点击缴费
- **Then**: 系统从用户余额扣款，账单状态更新为已缴费，生成缴费记录
- **Verification**: `programmatic`

### AC-3: 水费缴费
- **Given**: 用户已登录，存在待缴水费账单
- **When**: 用户进入水费页面，查看账单并点击缴费
- **Then**: 系统从用户余额扣款，账单状态更新为已缴费，生成缴费记录
- **Verification**: `programmatic`

### AC-4: 燃气费缴费
- **Given**: 用户已登录，存在待缴燃气费账单
- **When**: 用户进入燃气费页面，查看账单并点击缴费
- **Then**: 系统从用户余额扣款，账单状态更新为已缴费，生成缴费记录
- **Verification**: `programmatic`

### AC-5: 分类查看缴费记录
- **Given**: 用户已登录，有多条不同类型的缴费记录
- **When**: 用户进入缴费记录页面，选择费用类型筛选
- **Then**: 系统展示对应类型的历史缴费记录列表，包含金额、时间、状态
- **Verification**: `programmatic`

### AC-6: 计费规则查看
- **Given**: 用户访问系统
- **When**: 用户进入计费规则页面
- **Then**: 系统展示电费、水费、燃气费的计费标准和阶梯价格说明
- **Verification**: `human-judgment`
- **Notes**: 信息展示清晰易懂，分类型展示

### AC-7: 故障报修
- **Given**: 用户已登录
- **When**: 用户填写报修表单（类型、描述、地址）并提交
- **Then**: 系统创建报修工单，用户可查看报修列表和工单状态
- **Verification**: `programmatic`

### AC-8: 账户余额管理
- **Given**: 用户已登录
- **When**: 用户进行充值操作
- **Then**: 账户余额增加，可查询余额和充值记录
- **Verification**: `programmatic`

### AC-9: 代码上传 GitHub
- **Given**: 项目开发完成
- **When**: 代码推送到 GitHub 仓库
- **Then**: 仓库包含完整前后端代码、README 说明、部署文档
- **Verification**: `human-judgment`

## Open Questions
- 暂无
