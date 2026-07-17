# Library P0 Run13 Frontend

# 系统架构文档

## 1. 概述

- **项目**：Library P0 Run13
- **需求摘要**：开发一个图书管理系统，包含图书借阅、归还、读者管理、查询统计

## 2. 架构风格

- 前后端分离
- RESTful API
- 分层架构：Controller → Service → Repository

## 3. 技术栈

- Python
- FastAPI

## 4. 模块划分

| 模块 | 说明 |
|------|------|
| backend | API 服务、业务逻辑、数据访问 |
| frontend | Web 界面 |
| database | 数据模型与迁移 |
| tests | 单元测试与集成测试 |

## 5. 核心 API（草案）

- `GET /api/health` — 健康检查
- `GET /api/items` — 列表查询
- `POST /api/items` — 创建资源
- `PUT /api/items/{id}` — 更新资源
- `DELETE /api/items/{id}` — 删除资源

## 6. 数据模型（草案）

- User — 用户
- Item — 核心业务实体

## 7. 参考 PRD 摘要

# 产品需求文档 (PRD) — 图书管理系统

## 1. 项目概述

开发
