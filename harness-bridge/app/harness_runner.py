"""harness headless 执行器：运行 dsh CLI 并逐行产出事件流。"""
from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator, Dict, Any, List, Optional


class HarnessRunner:
    """封装一次 harness headless 进程调用，产出中性事件 dict。"""

    def __init__(
        self,
        harness_dir: str,
        patch_path: str,
        message: str,
        env: Optional[Dict[str, str]] = None,
        timeout_s: int = 300,
    ):
        self.dsh_dir = harness_dir
        self.patch_path = patch_path
        self.message = message
        self.env = env or {}
        self.timeout = timeout_s
        self._final_lines: List[str] = []

    async def run(self) -> Dict[str, Any]:
        """同时读取 stdout(answer) 与 stderr(reasoning)，返回结果映射。"""
        result = {"reasoning": [], "answer": ""}
        # Windows 下 pnpm 是 pnpm.cmd，需显式指定；否则用 pnpm。
        pnpm_bin = "pnpm.cmd" if os.name == "nt" else "pnpm"
        cmd = [
            pnpm_bin, "dsh", "--profile", "headless",
            "--patch", self.patch_path,
            self.message,
        ]
        merged_env = {**os.environ, **self.env}
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.dsh_dir,
                env=merged_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            result["answer"] = f"无法启动 headless: pnpm 不存在于 {self.dsh_dir}"
            return result

        try:
            answer_lines, reasoning_lines = await asyncio.gather(
                self._drain_stdout(proc),
                self._drain_stderr(proc),
            )
            result["answer"] = "\n".join(answer_lines).strip()
            if reasoning_lines:
                result["reasoning"] = reasoning_lines
        finally:
            try:
                await proc.wait()
            except ProcessLookupError:
                pass
        return result

    async def _drain_stdout(self, proc) -> List[str]:
        """读取 stdout，过滤插件加载日志与 dsh 前缀，返回 answer 行。"""
        lines: List[str] = []
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\n")
                if not text.strip():
                    continue
                if text.startswith("["):  # 插件加载日志
                    continue
                if text.startswith("dsh:"):
                    continue
                lines.append(text)
        except (AttributeError, RuntimeError):
            pass
        return lines

    async def _drain_stderr(self, proc) -> List[str]:
        """读取 stderr，把 dsh: reasoning 块折叠为列表。"""
        chunks: List[str] = []
        current: List[str] = []
        try:
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\n")
                if not text.strip():
                    continue
                if text.startswith("dsh: reasoning:"):
                    payload = text[len("dsh: reasoning:"):].strip()
                    if current:
                        chunks.append("\n".join(current).strip())
                        current = []
                    if payload:
                        current.append(payload)
                elif text.startswith("dsh:"):
                    continue
                elif text.startswith("$ "):
                    continue  # stderr 里的命令行回显，如 "$ node --import ..."
                else:
                    current.append(text)
            if current:
                chunks.append("\n".join(current).strip())
        except (ConnectionError, RuntimeError):
            pass
        return [c for c in chunks if c]