// API 客户端：统一封装，BASE_URL 指向 Control Plane
import axios from 'axios';

// 后端地址：Vite 开发时可配置 VITE_API_BASE，默认 localhost:8080
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';

const http = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// 请求拦截：自动附加 JWT（若有）
const TOKEN_KEY = 'agent_platform_token';
export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || '';
}
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：401 时自动尝试重新认证并重放原请求（后端恢复后前端自动恢复真实链路，而非停留 mock）
let authReplaying = false;
http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const cfg = err.config;
    if (err.response?.status === 401 && cfg && !cfg._authRetried && !authReplaying) {
      cfg._authRetried = true;
      authReplaying = true;
      try {
        const ok = await ensureAuth();
        if (ok) {
          // 携带新 token 重放原请求
          return await http(cfg);
        }
      } catch {
        // 忽略，进入 reject
      } finally {
        authReplaying = false;
      }
    }
    if (err.response?.status === 401) {
      clearToken();
    }
    return Promise.reject(err);
  }
);

export default http;

// ============ 鉴权引导（演示 / 离线连接用） ============
// 前端无登录页，连接后端时自动使用默认测试账号换取 token。
// 优先登录，失败则注册，保证一次连接即可看到后端数据。
const DEV_EMAIL = 'test@example.com';
const DEV_PASSWORD = 'password123';
const DEV_USERNAME = 'testuser';

// 解析 JWT payload（base64url -> JSON），用于判断 token 是否过期。
// 纯前端实现，不引入第三方库；解析失败按"未过期"处理（后端 401 会再兜底）。
function jwtPayload(token: string): { exp?: number } | null {
  try {
    const seg = token.split('.')[1];
    if (!seg) return null;
    const b64 = seg.replace(/-/g, '+').replace(/_/g, '/');
    const padded = b64.padEnd(Math.ceil(b64.length / 4) * 4, '=');
    const json = decodeURIComponent(
      atob(padded)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

// token 是否仍有效（存在且未过期）。过期则清除并返回 false，触发重新登录。
export function isTokenValid(): boolean {
  const token = getToken();
  if (!token) return false;
  const payload = jwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return true; // 无法解析视为有效
  return payload.exp * 1000 > Date.now();
}

export async function ensureAuth(): Promise<boolean> {
  // 有 token 但已过期时强制重登（避免 401 重试死循环回退 mock）
  if (isTokenValid()) return true;
  clearToken();

  // 用裸 fetch 避免依赖拦截器
  const tryLogin = async () => {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: DEV_EMAIL, password: DEV_PASSWORD }),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.access_token as string;
  };

  // 登录
  let token = await tryLogin().catch(() => null);
  // 登录失败（用户不存在）则注册后重试
  if (!token) {
    try {
      await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: DEV_EMAIL, username: DEV_USERNAME, password: DEV_PASSWORD }),
      });
      token = await tryLogin();
    } catch {
      token = null;
    }
  }

  if (token) {
    setToken(token);
    return true;
  }
  return false;
}

export { DEV_EMAIL };