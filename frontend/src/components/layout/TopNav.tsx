import { useState } from 'react';
import { Bell, ChevronDown, Search } from 'lucide-react';

export default function TopNav() {
  const [active, setActive] = useState('产品管理');

  const menuItems = ['产品管理', '资产管理', '报表管理'];

  return (
    <header className="h-[52px] bg-gradient-to-r from-[#0b1e3c] via-[#0e2a5c] to-[#123b7a] text-white flex items-center px-5 shrink-0 relative z-20 shadow-[0_2px_8px_rgba(0,0,0,0.15)]">
      {/* 左：Logo + 一级菜单 */}
      <div className="flex items-center gap-8 mr-auto">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#38b6ff] to-[#0077ff] flex items-center justify-center shadow-lg shadow-[#0077ff]/30">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L20 7V17L12 22L4 17V7L12 2Z" stroke="white" strokeWidth="1.6" fill="none" strokeLinejoin="round" />
              <path d="M12 8V16M12 8L9 10.5M12 8L15 10.5M8 14L12 16L16 14" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div className="leading-tight">
            <div className="text-[15px] font-semibold tracking-wide">DataAgent</div>
            <div className="text-[10px] text-blue-200/70 -mt-0.5">自主规划平台</div>
          </div>
        </div>

        {/* 一级菜单 */}
        <nav className="flex items-center gap-1">
          {menuItems.map((label) => (
            <button
              key={label}
              onClick={() => setActive(label)}
              className={`px-4 py-1.5 rounded-md text-[13px] transition-all ${
                active === label
                  ? 'bg-white/12 text-white font-medium'
                  : 'text-blue-100/80 hover:text-white hover:bg-white/8'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* 右：全局搜索 + 领域空间 + 用户 */}
      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md bg-white/10 text-[12px] text-blue-100/70 w-44">
          <Search size={13} />
          <span>全局搜索</span>
        </div>

        <button className="flex items-center gap-1 px-3 py-1.5 rounded-md text-[13px] text-blue-100/80 hover:text-white hover:bg-white/10 transition-colors">
          领域空间
          <ChevronDown size={13} className="text-blue-200/60" />
        </button>

        <button className="flex items-center gap-1 px-3 py-1.5 rounded-md text-[13px] text-blue-100/80 hover:text-white hover:bg-white/10 transition-colors">
          运营管理
        </button>

        <div className="w-px h-5 bg-white/15" />

        <button className="relative w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
          <Bell size={15} />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full border border-[#0e2a5c]" />
        </button>

        <button className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-md hover:bg-white/10 transition-colors">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-orange-400 to-pink-500 text-white flex items-center justify-center text-xs font-medium shadow">
            唐
          </div>
          <span className="text-[13px]">唐晓宇</span>
          <ChevronDown size={13} className="text-blue-200/60" />
        </button>
      </div>
    </header>
  );
}