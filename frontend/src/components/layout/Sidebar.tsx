import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  AppWindow,
  MessagesSquare,
  FileSearch,
  Blocks,
  Wand2,
  FileText,
  Cog,
  Network,
  Database,
  Table2,
  ClipboardCheck,
  ListChecks,
  Users,
  ChevronDown,
  ChevronRight,
  HelpCircle,
} from 'lucide-react';

interface MenuItem {
  to: string;
  label: string;
  icon: typeof AppWindow;
}

interface MenuGroup {
  label: string;
  items: MenuItem[];
}

const MENU_GROUPS: MenuGroup[] = [
  {
    label: 'AI应用管理',
    items: [
      { to: '/agents', label: 'Agent应用', icon: AppWindow },
      { to: '/chat', label: '产品问数', icon: MessagesSquare },
      { to: '/chat?prod=data', label: '数据解读', icon: FileSearch },
    ],
  },
  {
    label: '资源库',
    items: [
      { to: '/agents', label: 'Agent', icon: Blocks },
      { to: '/resources', label: 'Skill管理', icon: Wand2 },
      { to: '/resources?tab=prompt', label: '提示词', icon: FileText },
      { to: '/resources?tab=kb', label: '知识库', icon: Database },
      { to: '/resources?tab=tool', label: '工具', icon: Cog },
      { to: '/resources?tab=ontology', label: '本体', icon: Network },
      { to: '/resources?tab=ds', label: '数据源', icon: Table2 },
    ],
  },
  {
    label: 'Agent评测',
    items: [
      { to: '/evaluation', label: '评测集管理', icon: ClipboardCheck },
      { to: '/evaluation', label: '评测任务', icon: ListChecks },
    ],
  },
  {
    label: '空间管理',
    items: [
      { to: '/workspace', label: '空间成员与信息', icon: Users },
    ],
  },
];

function isItemActive(item: MenuItem, pathname: string, search: string): boolean {
  const itemPath = item.to.split('?')[0];
  if (itemPath === '/agents') {
    return pathname === '/agents' || pathname.startsWith('/agents/');
  }
  // 资源库多个 tab 用 query 区分，完整匹配（path + query）
  return (pathname + search) === item.to;
}

export default function Sidebar() {
  const { pathname, search } = useLocation();
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  const toggleGroup = (label: string) => {
    setCollapsed((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  return (
    <aside className="w-[216px] bg-white border-r border-[#e8e9ec] flex flex-col shrink-0">
      {/* 空间栏 */}
      <div className="h-[52px] flex items-center justify-between px-4 border-b border-[#f0f1f3] bg-[#fafbfc]">
        <div className="flex items-center gap-2 text-[13px] text-[#1d2129]">
          <div className="w-6 h-6 rounded bg-gradient-to-br from-emerald-400 to-teal-500 text-white flex items-center justify-center text-[11px] font-bold">
            U
          </div>
          <span className="font-medium">用户 HR 集成供应链</span>
        </div>
        <ChevronDown size={14} className="text-gray-300" />
      </div>

      {/* 返回领域空间 */}
      <button className="flex items-center gap-1.5 px-4 py-2.5 text-[12px] text-[#86909c] hover:text-[#0077ff] hover:bg-[#f7f9fc] border-b border-[#f2f3f5] transition-colors">
        <ChevronRight size={13} />
        返回领域空间
      </button>

      {/* 菜单 */}
      <nav className="flex-1 overflow-y-auto py-2">
        {MENU_GROUPS.map((group) => {
          const isCollapsed = collapsed[group.label];
          return (
            <div key={group.label} className="mb-2">
              <button
                onClick={() => toggleGroup(group.label)}
                className="w-full flex items-center justify-between px-4 py-2 text-[12px] font-medium text-[#86909c] hover:text-[#4e5969]"
              >
                <span>{group.label}</span>
                <ChevronDown
                  size={13}
                  className={`transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
                />
              </button>

              {!isCollapsed && (
                <div className="py-0.5">
                  {group.items.map((item) => {
                    const active = isItemActive(item, pathname, search);
                    return (
                      <NavLink
                        key={item.label}
                        to={item.to}
                        className={`relative flex items-center gap-2.5 mx-2 px-3 py-[9px] rounded-md text-[13px] border-l-[3px] transition-all ${
                          active
                            ? 'bg-[#e8f3ff] border-[#0077ff] text-[#0077ff] font-medium'
                            : 'border-transparent text-[#4e5969] hover:bg-[#f5f7fa] hover:text-[#0077ff]'
                        }`}
                      >
                        <item.icon
                          size={16}
                          strokeWidth={active ? 2.2 : 1.8}
                          className={active ? '' : 'text-[#86909c] group-hover:text-current'}
                        />
                        {item.label}
                      </NavLink>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* 底部帮助 */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-[#f2f3f5]">
        <HelpCircle size={15} className="text-gray-300" />
        <span className="text-[12px] text-[#86909c]">帮助与文档</span>
      </div>
    </aside>
  );
}