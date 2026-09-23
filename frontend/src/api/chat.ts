// Chat / Run API：对接 Control Plane 会话与 SSE
import http, { API_BASE, getToken } from '../utils/request';

export interface RunResult {
  run_id: string;
  status: string;
}

// 创建/获取调试会话（复用单会话模式，有则用，无则建）
const SESSION_KEY = 'agent_demo_session_id';

export function getCachedSessionId(): string | null {
  return localStorage.getItem(SESSION_KEY);
}
export function cacheSessionId(sid: string) {
  localStorage.setItem(SESSION_KEY, sid);
}

export async function ensureSession(model = 'Qwen3.5-397b-a17b'): Promise<string> {
  const cached = getCachedSessionId();
  if (cached) return cached;

  const { data } = await http.post('/sessions', { title: 'Agent 调试会话', model });
  setSessionId(data.id);
  return data.id;
}

function setSessionId(sid: string) {
  localStorage.setItem(SESSION_KEY, sid);
}

// 发送消息启动 Run
export async function startRun(sessionId: string, content: string, agent?: { id: string; name: string }) {
  const { data } = await http.post(`/sessions/${sessionId}/runs`, {
    content,
    agent: agent || undefined,
  });
  return data as { run_id: string; status: string };
}

// 订阅 SSE 事件流，回调每个 Trace Contract 事件
// 事件结构：{ type, content: Step }
export async function streamRun(
  sessionId: string,
  onEvent: (type: string, step: any) => void,
  signal?: AbortSignal
): Promise<void> {
  const resp = await fetch(`${API_BASE}/sessions/${sessionId}/stream`, {
    headers: { Authorization: `Bearer ${getToken()}` },
    signal,
  });

  if (!resp.ok || !resp.body) {
    throw new Error(`stream failed: ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // 按空行分隔 SSE
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';
    for (const raw of events) {
      for (const line of raw.split('\n')) {
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.slice(6));
            onEvent(parsed.type, parsed.content || {});
          } catch {
            // 忽略解析失败
          }
        }
      }
    }
  }
}

// 历史 Trace（备用，重放）
export async function getRunEvents(sessionId: string, runId: string) {
  const { data } = await http.get(`/sessions/${sessionId}/runs/${runId}/events`);
  return data.events as { type: string; content: any }[];
}