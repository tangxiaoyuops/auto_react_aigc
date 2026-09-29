"""临时启动脚本：新 control-plane 实例（端口 8090）
与 start_control_plane.py 相同的 PYTHONPATH/chdir 注入，仅改端口，
用于读取新 .env(COGNITION_URL=http://localhost:8600) 而无需杀掉旧 8080 实例。
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "control-plane"))
sys.path.insert(0, str(project_root / "shared"))

os.chdir(project_root / "control-plane")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
    )
