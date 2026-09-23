import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Edit3,
  MessageSquare,
  Trash2,
  Search,
  Bot,
  Layers,
  PlayCircle,
} from 'lucide-react';
import { useAgentStore } from '../../stores/agentStore';

const STATUS_FILTERS = [
  { value: 'all', label: '全部' },
  { value: 'published', label: '已上架' },
  { value: 'draft', label: '未上架' },
  { value: 'offline', label: '已下线' },
];

const STATUS_STYLE: Record<string, { label: string; cls: string; dot: string }> = {
  published: { label: '已上架', cls: 'bg-emerald-50 text-emerald-600', dot: 'bg-emerald-500' },
  draft: { label: '未上架', cls: 'bg-orange-50 text-orange-600', dot: 'bg-orange-400' },
  offline: { label: '已下线', cls: 'bg-gray-100 text-gray-500', dot: 'bg-gray-400' },
};

export default function AgentList() {
  const navigate = useNavigate();
  const agents = useAgentStore((s) => s.agents);
  const deleteAgent = useAgentStore((s) => s.deleteAgent);

  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filtered = agents.filter((a) => {
    const matchKw = !keyword || a.name.toLowerCase().includes(keyword.toLowerCase());
    const matchStatus = statusFilter === 'all' || a.status === statusFilter;
    return matchKw && matchStatus;
  });

  const publishedCount = agents.filter((a) => a.status === 'published').length;

  return (
    <div className="p-6">
      {/* 页头 */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-semibold text-[#1d2129]">Agent管理</h1>
          <p className="text-[13px] text-[#86909c] mt-1">创建、配置并发布你的智能体</p>
        </div>
        <button
          onClick={() => navigate('/agents/new')}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
        >
          <Plus size={16} /> 新建Agent
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-5">
        <StatCard
          icon={<Bot size={18} />}
          label="Agent总数"
          value={agents.length}
          iconCls="bg-blue-50 text-[#0077ff]"
        />
        <StatCard
          icon={<PlayCircle size={18} />}
          label="已上架"
          value={publishedCount}
          iconCls="bg-emerald-50 text-emerald-500"
        />
        <StatCard
          icon={<Layers size={18} />}
          label="未上架"
          value={agents.length - publishedCount}
          iconCls="bg-orange-50 text-orange-500"
        />
        <div className="panel p-4 flex flex-col justify-center bg-gradient-to-br from-[#0077ff] to-[#005ed9] text-white border-0 shadow-[0_4px_12px_rgba(0,119,255,0.25)]">
          <div className="text-[12px] text-blue-100">平台提示</div>
          <div className="text-[13px] mt-1 leading-relaxed text-blue-50">
            上架后 Agent 即可在
            <br />
            产品问数中被调用
          </div>
        </div>
      </div>

      {/* 内容卡片 */}
      <div className="panel overflow-hidden">
        {/* 工具栏 */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#f0f1f3]">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#86909c]" />
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="搜索Agent名称 / ID"
              className="w-64 pl-9 pr-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] bg-white focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
            />
          </div>

          <div className="flex gap-1 bg-[#f2f3f5] rounded-md p-0.5">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={`px-3 py-1.5 rounded text-[13px] transition-all ${
                  statusFilter === f.value
                    ? 'bg-white text-[#1d2129] shadow-sm font-medium'
                    : 'text-[#86909c] hover:text-[#4e5969]'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <span className="ml-auto text-[12px] text-[#86909c]">
            共 {filtered.length} 个 Agent
          </span>
        </div>

        {/* 表格 */}
        {filtered.length === 0 ? (
          <EmptyState />
        ) : (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left bg-[#fafbfc] border-b border-[#f0f1f3]">
                <th className="py-3 px-4 font-medium text-[#86909c]">名称</th>
                <th className="py-3 px-3 font-medium text-[#86909c]">描述</th>
                <th className="py-3 px-3 font-medium text-[#86909c]">模型</th>
                <th className="py-3 px-3 font-medium text-[#86909c]">版本</th>
                <th className="py-3 px-3 font-medium text-[#86909c]">状态</th>
                <th className="py-3 px-4 font-medium text-[#86909c] text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((agent) => {
                const st = STATUS_STYLE[agent.status] || STATUS_STYLE.offline;
                return (
                  <tr
                    key={agent.id}
                    className="border-b border-[#f5f6f8] hover:bg-[#f7f9fc] transition-colors group"
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#38b6ff] to-[#0077ff] text-white flex items-center justify-center text-[13px] font-bold shadow-sm shrink-0">
                          {agent.name.slice(0, 1)}
                        </div>
                        <div>
                          <button
                            onClick={() => navigate(`/agents/${agent.id}`)}
                            className="font-medium text-[#1d2129] hover:text-[#0077ff] text-left"
                          >
                            {agent.name}
                          </button>
                          <div className="text-[11px] text-[#c0c4cc] mt-0.5">
                            ID: {agent.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-3 text-[#4e5969] max-w-[260px]">
                      <span className="line-clamp-1 block">{agent.description || '暂无描述'}</span>
                    </td>
                    <td className="py-4 px-3">
                      <span className="inline-flex items-center px-2 py-1 bg-[#f7f8fa] border border-[#ececf0] rounded text-[12px] text-[#4e5969]">
                        {agent.model}
                      </span>
                    </td>
                    <td className="py-4 px-3 text-[#86909c]">v{agent.version}</td>
                    <td className="py-4 px-3">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[12px] ${st.cls}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
                        {st.label}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => navigate(`/agents/${agent.id}`)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[12px] text-[#4e5969] hover:text-[#0077ff] hover:bg-[#e8f3ff] transition-colors"
                        >
                          <Edit3 size={13} /> 配置
                        </button>
                        <button
                          onClick={() => navigate(`/chat?agent=${agent.id}`)}
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded text-[12px] text-[#4e5969] hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                        >
                          <MessageSquare size={13} /> 对话
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`确定删除 "${agent.name}" 吗？`)) deleteAgent(agent.id);
                          }}
                          className="flex items-center gap-1 px-2 py-1.5 rounded text-[12px] text-[#c0c4cc] hover:text-red-500 hover:bg-red-50 transition-colors"
                          title="删除"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  iconCls,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  iconCls: string;
}) {
  return (
    <div className="panel p-4 flex items-center gap-3.5">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${iconCls}`}>
        {icon}
      </div>
      <div>
        <div className="text-[26px] font-semibold text-[#1d2129] leading-tight">{value}</div>
        <div className="text-[12px] text-[#86909c]">{label}</div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-16 h-16 rounded-full bg-[#f2f3f5] flex items-center justify-center mb-4">
        <Bot size={28} className="text-[#c0c4cc]" />
      </div>
      <p className="text-[14px] text-[#86909c]">暂无符合条件的 Agent</p>
      <p className="text-[12px] text-[#c0c4cc] mt-1">尝试更换搜索条件或新建 Agent</p>
    </div>
  );
}