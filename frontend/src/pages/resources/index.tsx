import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  Network,
  Wrench,
  Plus,
  FileText,
  Search,
  Database,
  MoreHorizontal,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { KNOWLEDGE_POOL, ONTOLOGY_POOL, SKILL_POOL } from '../../mock/agents';

type TabKey = 'kb' | 'skill' | 'prompt' | 'ontology' | 'ds';

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'kb', label: '知识库', icon: <Database size={15} /> },
  { key: 'skill', label: 'Skill', icon: <Wrench size={15} /> },
  { key: 'prompt', label: '提示词', icon: <FileText size={15} /> },
  { key: 'ontology', label: '本体', icon: <Network size={15} /> },
  { key: 'ds', label: '数据源', icon: <BookOpen size={15} /> },
];

interface ResourceItem {
  id: string;
  name: string;
  description: string;
  meta: string;
  tag: string;
  tagCls: string;
}

export default function Resources() {
  const [params, setParams] = useSearchParams();
  const queryTab = params.get('tab') as string | null;
  const validTab: TabKey =
    queryTab && TABS.some((t) => t.key === queryTab) ? (queryTab as TabKey) : 'kb';
  const [tab, setTab] = useState<TabKey>(validTab);
  const [keyword, setKeyword] = useState('');

  const dataMap: Record<TabKey, ResourceItem[]> = {
    kb: KNOWLEDGE_POOL.map((k) => ({
      ...k,
      meta: `${(Number(k.id.replace(/\D/g, '')) % 20) + 3} 个文档 · 最近更新 2026-09-${String((Number(k.id.replace(/\D/g, '')) % 15) + 1).padStart(2, '0')}`,
      tag: '已挂载',
      tagCls: 'bg-[#e8f3ff] text-[#0077ff]',
    })).slice(0, 6),
    skill: SKILL_POOL.map((s) => ({
      ...s,
      meta: 'v2.3 · Agent流程封装 · 启用中',
      tag: '已启用',
      tagCls: 'bg-emerald-50 text-emerald-600',
    })).slice(0, 6),
    prompt: [
      { id: 'p1', name: '通用客服提示词', description: '面向客户的通用问答提示词模板，涵盖礼貌话术与标准回复格式', meta: 'v1.5 · 引用 Agent：客服助手', tag: '被引用 3 次', tagCls: 'bg-violet-50 text-violet-500' },
      { id: 'p2', name: '数据分析提示词', description: '数据分析场景专属提示词，引导模型输出结构化分析结论', meta: 'v1.2 · 引用 Agent：数据解读', tag: '被引用 2 次', tagCls: 'bg-violet-50 text-violet-500' },
    ],
    ontology: ONTOLOGY_POOL.map((o) => ({
      ...o,
      meta: '本体语义 1.0 · 24 个概念',
      tag: '已挂载',
      tagCls: 'bg-[#e8f3ff] text-[#0077ff]',
    })).slice(0, 6),
    ds: [
      { id: 'ds1', name: '业务数仓 DWS', description: '企业业务数据仓库，覆盖销售、财务、生产等主题域（示例）', meta: '类型：ClickHouse · 延迟 ≤5s', tag: '已接入', tagCls: 'bg-teal-50 text-teal-600' },
      { id: 'ds2', name: '法规政策库', description: '法规政策数据接入源，结构化后供检索增强（示例）', meta: '类型：PostgreSQL · 每日同步', tag: '已接入', tagCls: 'bg-teal-50 text-teal-600' },
    ],
  };

  const list = dataMap[tab].filter(
    (item) => !keyword || item.name.toLowerCase().includes(keyword.toLowerCase())
  );

  const handleTabChange = (key: TabKey) => {
    setTab(key);
    setParams(key === 'kb' ? {} : { tab: key });
  };

  const TAB_TITLE: Record<TabKey, string> = {
    kb: '知识库',
    skill: 'Skill',
    prompt: '提示词',
    ontology: '本体',
    ds: '数据源',
  };

  const TAB_ICON: Record<TabKey, React.ReactNode> = {
    kb: <Database size={18} />,
    skill: <Wrench size={18} />,
    prompt: <FileText size={18} />,
    ontology: <Network size={18} />,
    ds: <BookOpen size={18} />,
  };

  return (
    <div className="p-6">
      {/* 页头 */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-semibold text-[#1d2129]">资源库</h1>
          <p className="text-[13px] text-[#86909c] mt-1">管理 Skill、提示词、知识库、本体与数据源，为 Agent 提供能力底座</p>
        </div>
        <button
          onClick={() => alert(`新建${TAB_TITLE[tab]}`)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
        >
          <Plus size={16} /> 新建{TAB_TITLE[tab]}
        </button>
      </div>

      {/* Tab */}
      <div className="flex gap-6 border-b border-[#e5e6eb] mb-5">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => handleTabChange(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-[13px] border-b-2 -mb-px transition-colors ${
              tab === t.key
                ? 'border-[#0077ff] text-[#0077ff] font-medium'
                : 'border-transparent text-[#86909c] hover:text-[#4e5969]'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* 工具栏 */}
      <div className="flex items-center mb-4">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#86909c]" />
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder={`搜索${TAB_TITLE[tab]}名称`}
            className="w-64 pl-9 pr-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] bg-white focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
          />
        </div>
        <span className="ml-auto text-[12px] text-[#86909c] flex items-center gap-1">
          <Layers size={13} />
          共 {list.length} 项
        </span>
      </div>

      {/* 列表 */}
      {list.length === 0 ? (
        <div className="panel py-16 text-center">
          <div className="w-14 h-14 rounded-full bg-[#f2f3f5] flex items-center justify-center mx-auto mb-3">
            <Database size={24} className="text-[#c0c4cc]" />
          </div>
          <p className="text-[14px] text-[#86909c]">暂无{TAB_TITLE[tab]}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
          {list.map((item) => (
            <div
              key={item.id}
              className="panel group p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-11 h-11 rounded-lg text-white flex items-center justify-center bg-gradient-to-br ${
                  tab === 'kb' ? 'from-[#38b6ff] to-[#0077ff]' :
                  tab === 'skill' ? 'from-amber-400 to-orange-500' :
                  tab === 'prompt' ? 'from-violet-400 to-purple-500' :
                  tab === 'ontology' ? 'from-cyan-400 to-teal-500' :
                  'from-slate-400 to-slate-500'
                }`}>
                  {TAB_ICON[tab]}
                </div>
                <button className="w-8 h-8 rounded-md text-[#c0c4cc] hover:text-[#4e5969] hover:bg-[#f2f3f5] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <MoreHorizontal size={16} />
                </button>
              </div>

              <h3 className="text-[14px] font-medium text-[#1d2129] group-hover:text-[#0077ff] transition-colors">
                {item.name}
              </h3>
              <p className="text-[12px] text-[#86909c] mt-1.5 leading-relaxed line-clamp-2 min-h-[36px]">
                {item.description}
              </p>

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#f2f3f5]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] whitespace-nowrap ${item.tagCls}`}>
                    {item.tag}
                  </span>
                  <span className="text-[11px] text-[#c0c4cc] truncate">{item.meta}</span>
                </div>
                <ChevronRight size={14} className="text-[#c0c4cc] shrink-0 group-hover:text-[#0077ff] group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}