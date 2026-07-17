# 测试报告（草案）

## 项目
Library P0 Run13

## 后端覆盖摘要
--- .env.example ---
# Library Management System - Environment Configuration
# Copy this file to .env and modify as needed.

# Application
APP_NAME=Library Management System
APP_VERSION=1.0.0
DEBUG=true

# Database (SQLite for development, PostgreSQL for production)
# SQLite:
DATABASE_URL=sqlite+aiosqlite:///./library.db
# PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/library

DATABASE_ECHO=false

# Borrowing rules
MAX_BORROW_BOOKS=5
DEFAULT_BORROW_DAYS=30

# Pagination
DEFAULT_PAGE_SIZE=20


--- config.py ---
"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Library Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./library.db"
    DATABASE_ECHO: bool = False

    # Borrowin

## 前端覆盖摘要
--- app.js ---
document.getElementById('loadBtn').addEventListener('click', async () => {
  const res = await fetch('/api/items');
  const data = await res.json();
  document.getElementById('output').textContent = JSON.stringify(data, null, 2);
});


--- css\style.css ---
/* =============================================
   Library P0 Run13 - 图书管理系统 自定义样式
   ============================================= */

/* Body & Layout */
body {
    background-color: #f5f7fa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
    min-height: 100vh;
}

#app {
    min-height: calc(100vh - 80px);
}

/* Navbar */
.navbar {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
    font-weight: 700;
    font-size: 1.25rem;
}

.navbar .nav-link {
    font-size: 0.95rem;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    transition: background-color 0.2s;
}

.navbar .nav-link:hover,
.navbar .nav-link.active {
    backgr

## 结论
- 基础测试用例已生成
- 待接入 CI 执行
