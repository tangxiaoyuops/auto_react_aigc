// Chat / Run API：对接 Control Plane 会话与 SSE
import http, { API_BASE, getToken, ensureAuth } from '../utils/request';

export interface RunResult {
  run_id: string;
  status: string;
}

// 创建/获取调试会话（按 Agent 隔离，有则用，无则建）
// key 依 agentId 区分，避免多个 Agent 的调试会话混在一起。
function sessionKey(agentId: string): string {
  return `agent_demo_session_id:${agentId || 'default'}`;
}
function getCachedSessionId(agentId: string): string | null {
  try {
    return localStorage.getItem(sessionKey(agentId));
  } catch {
    return null;
  }
}
function cacheSessionId(agentId: string, sid: string) {
  try {
    localStorage.setItem(sessionKey(agentId), sid);
  } catch {
    /* ignore */
  }
}

export interface SessionListItem {
  id: string;
  title?: string;
  model?: string;
  created_at?: string;
  updated_at?: string;
}

export async function listSessions(agentId: string): Promise<SessionListItem[]> {
  try {
    const { data } = await http.get(`/sessions`, { params: { agent_id: agentId, page_size: 50 } });
    return (data?.sessions || data || []) as SessionListItem[];
  } catch {
    return [];
  }
}

export async function createSession(
  agentId: string,
  title = 'Agent 调试会话',
  model = 'Qwen3.5-397b-a17b'
): Promise<string> {
  const { data } = await http.post('/sessions', {
    title,
    model,
    agent_id: agentId,
  });
  cacheSessionId(agentId, data.id);
  return data.id;
}

// 取某 session 的调试会话 id（有缓存且有则用，否则按 agent 新建）
export async function ensureSession(agentId: string, model = 'Qwen3.5-397b-a17b'): Promise<string> {
  const cached = getCachedSessionId(agentId);
  if (cached) {
    try {
      await http.get(`/sessions/${cached}`);
      return cached;
    } catch {
      try {
        localStorage.removeItem(sessionKey(agentId));
      } catch {
        /* ignore */
      }
    }
  }
  return createSession(agentId, 'Agent 调试会话', model);
}

export async function getSessionMessages(sessionId: string): Promise<Array<{ role: string; content: string; id?: string }>> {
  try {
    const { data } = await http.get(`/sessions/${sessionId}/messages`, { params: { limit: 200 } });
    return (data?.messages || []) as Array<{ role: string; content: string; id?: string }>;
  } catch {
    return [];
  }
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
  // 首次请求；若 401（token 失效）则 ensureAuth 刷新后重连一次
  for (let attempt = 0; attempt < 2; attempt++) {
    const resp = await fetch(`${API_BASE}/sessions/${sessionId}/stream`, {
      headers: { Authorization: `Bearer ${getToken()}` },
      signal,
    });

    if (resp.status === 401 && attempt === 0) {
      const ok = await ensureAuth();
      if (!ok) throw new Error('stream auth failed');
      continue; // 用刷新后的 token 重试
    }

    if (!resp.ok || !resp.body) {
      throw new Error(`stream failed: ${resp.status}`);
    }
    return consumeStream(resp.body, onEvent);
  }
  throw new Error('stream auth retry exhausted');
}

async function consumeStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (type: string, step: any) => void
): Promise<void> {
  const reader = body.getReader();
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