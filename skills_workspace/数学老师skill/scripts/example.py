"""示例脚本：Skill 的可执行 Python 脚本。

Agent 可通过运行 `scripts/<本文件名>` 调用本脚本。
请在入口处定义 main，接收字符串参数，返回结构化输出。
"""
import json
import sys
from typing import List


def main(argv: List[str]) -> dict:
    # 在此实现业务逻辑
    return {"ok": True, "args": argv}


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1:]), ensure_ascii=False, indent=2))
