@echo off
REM WebUI 快速验证脚本 (Windows)
REM 使用: 在项目根目录运行此脚本

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo AUTO-MAS-Lite WebUI 版本验证
echo ============================================================
echo.

REM 1. 检查环境
echo [1/4] 检查环境...
python --version >nul 2>&1 && echo ✅ Python 已安装 || echo ❌ Python 未安装
node --version >nul 2>&1 && echo ✅ Node.js 已安装 || echo ❌ Node.js 未安装
yarn --version >nul 2>&1 && echo ✅ Yarn 已安装 || echo ❌ Yarn 未安装
echo.

REM 2. 检查后端
echo [2/4] 检查后端...
timeout /t 1 /nobreak >nul
curl -s http://localhost:36163/docs >nul 2>&1
if !errorlevel! equ 0 (
    echo ✅ 后端已运行
) else (
    echo ⚠️  后端未运行 (这是正常的，需要手动启动)
)
echo.

REM 3. 检查前端
echo [3/4] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo ⚠️  node_modules 不存在，请运行: yarn install
) else (
    echo ✅ 前端依赖已就绪
)
cd ..
echo.

REM 4. 显示启动说明
echo [4/4] 准备就绪！
echo.
echo ============================================================
echo 启动步骤
echo ============================================================
echo.
echo 方式 1: 使用单个终端 (推荐)
echo   cd frontend
echo   yarn dev:fullstack
echo   然后打开 http://localhost:5173
echo.
echo 方式 2: 使用多个终端
echo   终端 1:
echo     python main.py
echo   终端 2:
echo     cd frontend
echo     yarn dev
echo   然后打开 http://localhost:5173
echo.
echo ============================================================
echo 验证清单
echo ============================================================
echo □ 后端运行在 http://localhost:36163
echo □ 前端运行在 http://localhost:5173
echo □ 页面正常加载
echo □ TitleBar 窗口控制按钮隐藏
echo □ 浏览器控制台无 Electron API 错误
echo □ localStorage 配置已保存
echo.
echo 详细清单见: docs-AI/web-validation-checklist.md
echo.
echo ============================================================
echo.
pause
