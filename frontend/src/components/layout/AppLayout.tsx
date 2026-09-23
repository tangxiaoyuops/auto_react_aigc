import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import TopNav from './TopNav';
import Sidebar from './Sidebar';
import { ensureAuth } from '../../utils/request';
import { useAgentStore } from '../../stores/agentStore';

export default function AppLayout() {
  // 启动：连接后端获取 token 并加载 Agent 列表（后端不可达时静默降级为 mock）
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await ensureAuth();
      if (!ok || cancelled) return;
      await useAgentStore.getState().fetchAgents();
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[#f5f6f8] text-gray-800 overflow-hidden">
      {/* 顶部一级导航 */}
      <TopNav />

      {/* 主体：侧边栏 + 内容 */}
      <div className="flex-1 flex min-h-0">
        <Sidebar />
        <main className="flex-1 min-w-0 overflow-y-auto bg-[#f5f6f8]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}