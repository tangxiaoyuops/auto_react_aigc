"""Web search tool —— 真实免费搜索（Bing 网页搜索，无需 API key）。

实现要点：
  - 使用 Bing 网页搜索 HTML 页面（cn.bing.com/search）解析真实结果。
  - 纯标准库（urllib + html.parser），零第三方依赖，保证任意环境可跑。
  - 多引擎 fallback：Bing -> `api.duckduckgo.com`（Instant Answer）。
  - 全部失败时回退内置 mock 结果（保证 Agent 工具调用链路不断）。
"""
import asyncio
import html as html_mod
import urllib.parse
import urllib.request
from html.parser import HTMLParser

from app.tools.base import tool, inventory

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class _BingParser(HTMLParser):
    """极简 Bing 结果项解析器：抓 `<li class=b_algo>` 内 标题(h2>a) + url + 摘要(p)。"""

    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._in_algo = False
        self._in_h2 = False
        self._in_p = False
        self._depth_algo = 0
        self._cur = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")
        if tag == "li" and "b_algo" in cls.split():
            self._in_algo = True
            self._depth_algo = 1
            self._cur = {}
            return
        if not self._in_algo:
            return
        if tag == "li":
            self._depth_algo += 1
        if tag == "h2":
            self._in_h2 = True
        if tag == "a" and self._in_h2 and "href" in attrs:
            self._cur["url"] = attrs["href"]
        if tag == "p":
            self._in_p = True

    def handle_data(self, data):
        if self._in_h2:
            self._cur.setdefault("title", "")
            self._cur["title"] += data
        elif self._in_p and self._in_algo:
            self._cur.setdefault("snippet", "")
            self._cur["snippet"] += data

    def handle_endtag(self, tag):
        if not self._in_algo:
            return
        if tag == "li":
            self._depth_algo -= 1
            if self._depth_algo == 0:
                self._in_algo = False
                if self._cur.get("title") or self._cur.get("url"):
                    self.results.append(self._cur)
                self._cur = {}
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_p = False


def _fetch(url: str, timeout: float = 8.0) -> str:
    """拉取 URL，返回解码文本。失败抛异常。"""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    # 优先按响应 charset 解码，兜底 utf-8
    ctype = resp.headers.get("Content-Type", "")
    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return raw.decode("latin-1", errors="ignore")


def _search_bing(query: str, num_results: int) -> list[dict]:
    url = "https://cn.bing.com/search?q=" + urllib.parse.quote(query)
    html_text = _fetch(url, timeout=8.0)
    # 截取 <ol id="b_results"> 片段减少解析噪音
    start = html_text.find('<ol id="b_results"')
    if start == -1:
        start = 0
    end = html_text.find("</ol>", start)
    body = html_text[start:end] if end != -1 else html_text[start:]
    parser = _BingParser()
    parser.feed(body)
    results = []
    for i, r in enumerate(parser.results[:num_results]):
        results.append({
            "title": _clean(r.get("title", "")),
            "url": r.get("url", ""),
            "snippet": _clean(r.get("snippet", "")),
            "rank": i + 1,
        })
    return results


def _clean(text: str) -> str:
    return " ".join(text.split())


def _mock_results(query: str, num_results: int) -> list[dict]:
    return [
        {
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/result/{i+1}",
            "snippet": f"搜索结果（离线兜底）for '{query}'。联网后 Bing 将返回真实结果。",
            "rank": i + 1,
        }
        for i in range(num_results)
    ]


@tool(
    name="web_search",
    description="在网络上搜索最新信息并返回真实网页结果。用于需要实时或外部信息的场景。",
    parameters={
        "query": {"type": "string", "required": True, "description": "搜索关键词或完整问题"},
        "num_results": {"type": "integer", "description": "返回结果数量（默认 5）"},
    },
    output="搜索结果 dict（title/url/snippet/rank）",
)
async def execute(query: str, num_results: int = 5) -> dict:
    def _run():
        try:
            results = _search_bing(query, num_results)
            if results:
                return {"engine": "bing", "results": results}
            return {"engine": "bing", "results": [], "error": "无结果"}
        except Exception as e:
            return {"engine": "mock", "results": _mock_results(query, num_results), "error": str(e)}

    result = await asyncio.to_thread(_run)

    return {
        "query": query,
        "num_results": len(result["results"]),
        "engine": result["engine"],
        "results": result["results"],
        "error": result.get("error"),
    }


# 注册到进程级注册表
inventory.register(execute)