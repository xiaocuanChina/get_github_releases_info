@echo off
chcp 65001 > nul
echo ========================================
echo    GitHub Releases 项目启动脚本
echo ========================================
echo.

REM 设置默认端口
set BACKEND_PORT=8000
set FRONTEND_PORT=8080

REM 检查.env文件是否存在
if exist .env (
    echo 正在从 .env 文件读取配置...

    REM 读取后端端口
    for /f "tokens=2 delims==" %%a in ('findstr "^BACKEND_PORT=" .env 2^>nul') do set BACKEND_PORT=%%a

    REM 读取前端端口
    for /f "tokens=2 delims==" %%a in ('findstr "^FRONTEND_PORT=" .env 2^>nul') do set FRONTEND_PORT=%%a

    echo 配置读取完成！
) else (
    echo 警告: .env 文件不存在，使用默认端口配置
    echo 后端端口: %BACKEND_PORT%
    echo 前端端口: %FRONTEND_PORT%
)

echo.
echo 启动配置:
echo 后端端口: %BACKEND_PORT%
echo 前端端口: %FRONTEND_PORT%
echo.

REM 启动后端服务
echo 正在启动后端服务...
start "后端服务" cmd /k "echo 后端服务启动中... && python main.py"

REM 等待2秒让后端先启动
timeout /t 2 /nobreak >nul

REM 启动前端服务
echo 正在启动前端服务...
start "前端服务" cmd /k "echo 前端服务启动中... && cd get_github_info_vue && npm run serve"

echo.
echo ========================================
echo 服务启动完成！
echo 前端地址: http://localhost:%FRONTEND_PORT%
echo 后端地址: http://localhost:%BACKEND_PORT%
echo ========================================
echo.
echo 提示:
echo - 如需修改端口，请编辑 .env 文件
echo - 前端和后端会在新的命令行窗口中启动
echo - 关闭对应窗口即可停止服务
echo.
pause
