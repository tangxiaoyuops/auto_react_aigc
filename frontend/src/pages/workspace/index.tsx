import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  UserPlus,
  Bot,
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  BarChart3,
  MessagesSquare,
  Wand2,
} from 'lucide-react';

interface Member {
  id: string;
  name: string;
  account: string;
  role: string;
  joinedAt: string;
  active: boolean;
}

const SEED_MEMBERS: Member[] = [
  { id: 'u1', name: '唐晓宇', account: 'admin@platform.com', role: '管理员', joinedAt: '2026-09-01', active: true },
  { id: 'u2', name: '张三', account: 'zhangsan@example.com', role: '成员', joinedAt: '2026-09-05', active: true },
  { id: 'u3', name: '李四', account: 'lisi@example.com', role: '成员', joinedAt: '2026-09-08', active: false },
];

const QUICK_ACTIONS = [
  { label: '新建Agent', desc: '创建智能体应用', to: '/agents/new', icon: Bot, bg: 'from-[#0077ff] to-[#0066dd]' },
  { label: '产品问数', desc: '与Agent对话', to: '/chat', icon: MessagesSquare, bg: 'from-violet-500 to-purple-600' },
  { label: 'Skill管理', desc: '沉淀专业能力', to: '/resources?tab=skill', icon: Wand2, bg: 'from-amber-500 to-orange-500' },
  { label: '评测管理', desc: '质量保障与回归', to: '/evaluation', icon: BarChart3, bg: 'from-emerald-500 to-teal-600' },
];

export default function Workspace() {
  const navigate = useNavigate();
  const [members, setMembers] = useState<Member[]>(SEED_MEMBERS);
  const [keyword, setKeyword] = useState('');
  const [showInvite, setShowInvite] = useState(false);
  const [inviteAccount, setInviteAccount] = useState('');

  const filtered = members.filter(
    (m) => !keyword || m.name.includes(keyword) || m.account.toLowerCase().includes(keyword.toLowerCase())
  );

  const handleInvite = () => {
    if (!inviteAccount.trim()) return;
    const newMember: Member = {
      id: `u${Date.now()}`,
      name: inviteAccount.split('@')[0],
      account: inviteAccount.trim(),
      role: '成员',
      joinedAt: new Date().toISOString().slice(0, 10),
      active: true,
    };
    setMembers((prev) => [...prev, newMember]);
    setInviteAccount('');
    setShowInvite(false);
  };

  const toggleActive = (id: string) => {
    setMembers((prev) => prev.map((m) => (m.id === id ? { ...m, active: !m.active } : m)));
  };

  return (
    <div className="p-6">
      {/* 渐变欢迎横幅 */}
      <div className="relative overflow-hidden rounded-panel-lg mb-6 bg-gradient-to-br from-[#0b1e3c] via-[#0e2a5c] to-[#123b7a] text-white px-8 py-7 shadow-[0_4px_20px_rgba(11,30,60,0.25)]">
        {/* 装饰圆 */}
        <div className="absolute -right-16 -top-20 w-64 h-64 rounded-full bg-[#0077ff]/20 blur-2xl" />
        <div className="absolute right-24 -bottom-24 w-56 h-56 rounded-full bg-violet-500/15 blur-2xl" />

        <div className="relative flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-[12px] text-blue-200/80 mb-2">
              <Sparkles size={13} />
              用户HR集成供应链 · 领域空间
            </div>
            <h1 className="text-[22px] font-semibold tracking-wide">欢迎回来，唐晓宇</h1>
            <p className="text-[13px] text-blue-200/70 mt-1.5">
              当前空间下已配置 <span className="text-white font-medium">4</span> 个 Agent，覆盖
              <span className="text-white font-medium"> 3 </span>个业务场景
            </p>
          </div>

          {/* 空间健康度 */}
          <div className="hidden md:flex items-center gap-6 bg-white/[0.08] backdrop-blur rounded-xl px-6 py-4 border border-white/10">
            <div className="text-center">
              <div className="text-[22px] font-semibold">98%</div>
              <div className="text-[11px] text-blue-200/70 mt-0.5">服务健康度</div>
            </div>
            <div className="w-px h-8 bg-white/15" />
            <div className="text-center">
              <div className="text-[22px] font-semibold">1.2k</div>
              <div className="text-[11px] text-blue-200/70 mt-0.5">本月调用</div>
            </div>
            <div className="w-px h-8 bg-white/15" />
            <div className="text-center">
              <div className="text-[22px] font-semibold">99.2%</div>
              <div className="text-[11px] text-blue-200/70 mt-0.5">意图识别成功率</div>
            </div>
          </div>
        </div>
      </div>

      {/* 快速入口 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a.label}
            onClick={() => navigate(a.to)}
            className="panel group p-4 flex items-center gap-3.5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all text-left"
          >
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${a.bg} text-white flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform`}>
              <a.icon size={18} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[14px] font-medium text-[#1d2129] flex items-center gap-1">
                {a.label}
                <ArrowUpRight size={13} className="text-[#c0c4cc] group-hover:text-[#0077ff] transition-colors" />
              </div>
              <div className="text-[12px] text-[#86909c] mt-0.5 truncate">{a.desc}</div>
            </div>
          </button>
        ))}
      </div>

      {/* 成员管理 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-[15px] font-semibold text-[#1d2129]">空间成员与信息</h2>
          <span className="text-[12px] text-[#c0c4cc]">共 {members.length} 人</span>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
        >
          <UserPlus size={16} /> 邀请成员
        </button>
      </div>

      <div className="panel overflow-hidden">
        {/* 工具栏 */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[#f0f1f3]">
          <div className="relative flex-1 max-w-xs">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#86909c]" />
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="搜索成员姓名或账号"
              className="w-full pl-9 pr-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] bg-white focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
            />
          </div>
          <span className="ml-auto text-[12px] text-[#86909c] flex items-center gap-1">
            <ShieldCheck size={13} className="text-emerald-500" />
            空间托管于企业组织体系
          </span>
        </div>

        {/* 成员表格 */}
        {filtered.length === 0 ? (
          <div className="py-16 text-center text-[#86909c] text-[13px]">未找到匹配的成员</div>
        ) : (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left bg-[#fafbfc] border-b border-[#f0f1f3]">
                <th className="py-3 px-5 font-medium text-[#86909c]">成员</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">账号</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">角色</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">加入时间</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">状态</th>
                <th className="py-3 px-5 font-medium text-[#86909c] text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m) => (
                <tr key={m.id} className="border-b border-[#f5f6f8] hover:bg-[#f7f9fc] transition-colors">
                  <td className="py-4 px-5">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-full text-white flex items-center justify-center text-xs font-medium ${
                          m.role === '管理员'
                            ? 'bg-gradient-to-br from-[#0077ff] to-indigo-600'
                            : 'bg-gradient-to-br from-[#38b6ff] to-[#0077ff]'
                        }`}
                      >
                        {m.name.slice(0, 1)}
                      </div>
                      <div>
                        <div className="font-medium text-[#1d2129]">{m.name}</div>
                        {m.role === '管理员' && (
                          <div className="text-[10px] text-[#0077ff] mt-0.5 flex items-center gap-0.5">
                            <ShieldCheck size={11} /> 空间所有者
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-[#4e5969]">{m.account}</td>
                  <td className="py-4 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-[12px] ${
                        m.role === '管理员'
                          ? 'bg-[#e8f3ff] text-[#0077ff]'
                          : 'bg-[#f7f8fa] text-[#4e5969]'
                      }`}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-[#86909c]">{m.joinedAt}</td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center gap-1.5 text-[12px] ${m.active ? 'text-emerald-600' : 'text-[#c0c4cc]'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${m.active ? 'bg-emerald-500' : 'bg-[#d4d7de]'}`} />
                      {m.active ? '正常' : '已停用'}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-right">
                    {m.role !== '管理员' && (
                      <button
                        onClick={() => toggleActive(m.id)}
                        className={`px-2.5 py-1 rounded-md text-[12px] transition-colors ${
                          m.active
                            ? 'text-[#c0c4cc] hover:text-red-500 hover:bg-red-50'
                            : 'text-[#0077ff] hover:bg-[#e8f3ff]'
                        }`}
                      >
                        {m.active ? '停用' : '启用'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 邀请成员弹窗 */}
      {showInvite && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={() => setShowInvite(false)}>
          <div className="bg-white rounded-panel-lg w-[420px] shadow-pop p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-[16px] font-semibold text-[#1d2129]">邀请成员</h3>
              <button onClick={() => setShowInvite(false)} className="w-7 h-7 rounded-md text-[#86909c] hover:bg-[#f2f3f5] flex items-center justify-center">✕</button>
            </div>
            <label className="block text-[12px] text-[#4e5969] mb-1.5">成员账号</label>
            <input
              value={inviteAccount}
              onChange={(e) => setInviteAccount(e.target.value)}
              placeholder="请输入成员账号"
              autoFocus
              className="w-full px-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
            />
            <p className="text-[11px] text-[#c0c4cc] mt-2">被邀请的成员将加入当前领域空间，默认角色为成员</p>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowInvite(false)}
                className="px-4 py-2 border border-[#d9d9d9] rounded-md text-[13px] text-[#4e5969] hover:border-[#0077ff] hover:text-[#0077ff] transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleInvite}
                className="px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors"
              >
                确认邀请
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}