@echo off
echo ========================================
echo  自主规划平台 - 快速启动脚本
echo ========================================
echo.

echo [1/2] 启动控制平面（简化版）...
start "控制平面" cmd /k "conda activate aigc_gragh_v1 && cd control-plane && python simple_main.py"
timeout /t 3 >nul

echo [2/2] 启动认知平面...
start "认知平面" cmd /k "conda activate aigc_gragh_v1 && cd cognition-plane && python -c \"from fastapi import FastAPI; from fastapi.responses import JSONResponse; app = FastAPI(); @app.get('/'); async def root(): return {'service': '认知平面', 'status': 'ready'}; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)\""
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
echo.
echo  按任意键打开API文档...
pause >nul
start http://localhost:8080/docs
