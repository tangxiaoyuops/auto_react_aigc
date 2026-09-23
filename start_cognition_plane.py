"""认知平面启动脚本"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "cognition-plane"))
sys.path.insert(0, str(project_root / "shared"))

# 切换到认知平面目录
os.chdir(project_root / "cognition-plane")

# 现在可以正常启动
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=[str(project_root / "cognition-plane")]
    )
