"""启动控制平面（单进程，供 M4 接口冒烟测试使用）。

与 start_control_plane.py 等效，但关闭 reload（避免占用 + 适合脚本自动运行）：
  - 设置 sys.path 包含 项目根 / control-plane / shared
  - 切换工作目录到 control-plane
  - 启动 uvicorn 单 worker
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
for p in (str(project_root), str(project_root / "control-plane"), str(project_root / "shared")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(project_root / "control-plane")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("CTRL_PORT", "8080")),
        reload=False,
        workers=1,
    )