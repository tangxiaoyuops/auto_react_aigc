@echo off
echo ========================================
echo  自主规划平台 - 完整版启动
echo ========================================
echo.

REM 设置项目根目录
cd /d "%~dp0"

echo [1/2] 启动控制平面...
start "控制平面 - Agent Platform" cmd /k "conda activate aigc_gragh_v1 && python start_control_plane.py"
timeout /t 5 >nul

echo [2/2] 启动认知平面...
start "认知平面 - Agent Platform" cmd /k "conda activate aigc_gragh_v1 && cd cognition-plane && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul

echo.
echo ========================================
echo  服务启动完成！
echo ========================================
echo.
echo  控制平面: http://localhost:8080
echo  控制平面API文档: http://localhost:8080/docs
echo.
echo  认知平面: http://localhost:8000
echo  认知平面API文档: http://localhost:8000/docs
echo.
echo  提示: 如果遇到错误，请查看各个窗口的输出
echo.
pause
