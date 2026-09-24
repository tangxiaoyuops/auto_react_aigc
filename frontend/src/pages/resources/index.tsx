import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  BookOpen,
  Network,
  Wrench,
  Plus,
  FileText,
  Search,
  Database,
  Layers,
  ChevronRight,
  Pencil,
  Trash2,
  Cog,
  X,
} from 'lucide-react';
import {
  RESOURCE_TAB_META,
  type ResourceItem,
  type ResourceType,
} from '../../api/resources';
import { useResourceStore } from '../../stores/resourceStore';

const TABS: { key: ResourceType; label: string; icon: React.ReactNode }[] = [
  { key: 'kb', label: '知识库', icon: <Database size={15} /> },
  { key: 'skill', label: 'Skill', icon: <Wrench size={15} /> },
  { key: 'prompt', label: '提示词', icon: <FileText size={15} /> },
  { key: 'ontology', label: '本体', icon: <Network size={15} /> },
  { key: 'ds', label: '数据源', icon: <BookOpen size={15} /> },
  { key: 'tool', label: '工具', icon: <Cog size={15} /> },
];

const ICON_CLS: Record<ResourceType, string> = {
  kb: 'from-[#38b6ff] to-[#0077ff]',
  skill: 'from-amber-400 to-orange-500',
  prompt: 'from-violet-400 to-purple-500',
  ontology: 'from-cyan-400 to-teal-500',
  ds: 'from-slate-400 to-slate-500',
  tool: 'from-emerald-400 to-teal-600',
};

interface FormState {
  id: string | null;
  name: string;
  description: string;
  content: string; // prompt/skill 的内容
}

const EMPTY_FORM: FormState = { id: null, name: '', description: '', content: '' };

export default function Resources() {
  const [params, setParams] = useSearchParams();
  const queryTab = params.get('tab') as string | null;
  const validTab: ResourceType =
    queryTab && TABS.some((t) => t.key === queryTab) ? (queryTab as ResourceType) : 'kb';
  const [tab, setTab] = useState<ResourceType>(validTab);
  const [keyword, setKeyword] = useState('');

  const byType = useResourceStore((s) => s.byType);
  const loaded = useResourceStore((s) => s.loaded);
  const fetchByType = useResourceStore((s) => s.fetchByType);
  const createResource = useResourceStore((s) => s.createResource);
  const updateResource = useResourceStore((s) => s.updateResource);
  const deleteResource = useResourceStore((s) => s.deleteResource);

  // 首次进入 + 切换 tab 时拉取对应类型
  useEffect(() => {
    if (!loaded[tab]) fetchByType(tab);
  }, [tab, loaded, fetchByType]);

  const [form, setForm] = useState<FormState | null>(null);

  const list: ResourceItem[] = (byType[tab] || []).filter(
    (item) => !keyword || item.name.toLowerCase().includes(keyword.toLowerCase())
  );

  const handleTabChange = (key: ResourceType) => {
    setTab(key);
    setParams(key === 'kb' ? {} : { tab: key });
  };

  const renderMeta = (item: ResourceItem): string => {
    const m = item.meta || {};
    if (tab === 'kb') {
      const n = Number(item.id.replace(/\D/g, '')) || 1;
      return `${(n % 20) + 3} 个文档 · ${m.index_status || '已建立索引'}`;
    }
    if (tab === 'skill') return `${m.version || 'v1.0'} · Agent流程封装 · 启用中`;
    if (tab === 'prompt') return `${m.version || 'v1.0'} · 模板`;
    if (tab === 'ontology') return `${m.version || '语义 1.0'} · ${m.concepts ?? '—'} 个概念`;
    if (tab === 'ds') return `类型：${m.conn_type || m.type || '—'} · 延迟 ≤5s`;
    if (tab === 'tool') return `类别：${m.category || '—'} · ${m.enabled === false ? '已停用' : '已启用'}`;
    return '';
  };

  const handleSave = async () => {
    if (!form) return;
    const meta: Record<string, any> = {};
    if (form.content) meta.content = form.content;
    if (tab === 'prompt' || tab === 'skill') meta.version = 'v1.0';
    if (tab === 'tool') meta.category = 'custom';
    if (form.id) {
      await updateResource(form.id, { name: form.name, description: form.description, meta });
    } else {
      await createResource({ type: tab, name: form.name, description: form.description, meta });
    }
    setForm(null);
  };

  const handleDelete = async (item: ResourceItem) => {
    if (!window.confirm(`确认删除「${item.name}」？`)) return;
    await deleteResource(tab, item.id);
  };

  return (
    <div className="p-6">
      {/* 页头 */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-semibold text-[#1d2129]">资源库</h1>
          <p className="text-[13px] text-[#86909c] mt-1">管理 Skill、提示词、知识库、本体、数据源与工具，为 Agent 提供能力底座</p>
        </div>
        <button
          onClick={() => setForm({ ...EMPTY_FORM })}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
        >
          <Plus size={16} /> {RESOURCE_TAB_META[tab].createLabel}
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
            placeholder={`搜索${RESOURCE_TAB_META[tab].label}名称`}
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
          <p className="text-[14px] text-[#86909c]">暂无{RESOURCE_TAB_META[tab].label}</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
          {list.map((item) => (
            <div
              key={item.id}
              className="panel group p-5 hover:shadow-card-hover hover:-translate-y-0.5 transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-11 h-11 rounded-lg text-white flex items-center justify-center bg-gradient-to-br ${ICON_CLS[tab]}`}>
                  {TABS.find((t) => t.key === tab)?.icon}
                </div>
                <div className="flex opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() =>
                      setForm({
                        id: item.id,
                        name: item.name,
                        description: item.description || '',
                        content: (item.meta?.content as string) || '',
                      })
                    }
                    className="w-8 h-8 rounded-md text-[#c0c4cc] hover:text-[#0077ff] hover:bg-[#f2f3f5] flex items-center justify-center"
                    title="编辑"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    onClick={() => handleDelete(item)}
                    className="w-8 h-8 rounded-md text-[#c0c4cc] hover:text-red-500 hover:bg-[#f2f3f5] flex items-center justify-center"
                    title="删除"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>

              <h3 className="text-[14px] font-medium text-[#1d2129] group-hover:text-[#0077ff] transition-colors">
                {item.name}
              </h3>
              <p className="text-[12px] text-[#86909c] mt-1.5 leading-relaxed line-clamp-2 min-h-[36px]">
                {item.description}
              </p>

              <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#f2f3f5]">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] whitespace-nowrap bg-[#e8f3ff] text-[#0077ff]">
                    {item.origin === 'seed' ? '内置' : '自建'}
                  </span>
                  <span className="text-[11px] text-[#c0c4cc] truncate">{renderMeta(item)}</span>
                </div>
                <ChevronRight size={14} className="text-[#c0c4cc] shrink-0 group-hover:text-[#0077ff] group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 新建/编辑弹窗 */}
      {form && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setForm(null)}>
          <div
            className="w-[520px] max-h-[80vh] overflow-y-auto bg-white rounded-xl shadow-xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-[16px] font-semibold text-[#1d2129]">
                {form.id ? `编辑${RESOURCE_TAB_META[tab].label}` : RESOURCE_TAB_META[tab].createLabel}
              </h2>
              <button onClick={() => setForm(null)} className="text-[#c0c4cc] hover:text-[#4e5969]">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-[13px] text-[#4e5969] mb-1.5">
                  <span className="text-red-500 mr-0.5">*</span>名称
                </label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
                  placeholder="请输入名称"
                />
              </div>

              <div>
                <label className="block text-[13px] text-[#4e5969] mb-1.5">描述</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
                  placeholder="资源描述"
                />
              </div>

              {(tab === 'prompt' || tab === 'skill') && (
                <div>
                  <label className="block text-[13px] text-[#4e5969] mb-1.5">
                    {tab === 'prompt' ? '提示词模板内容' : 'Skill 流程 / 提示词'}
                  </label>
                  <textarea
                    value={form.content}
                    onChange={(e) => setForm({ ...form, content: e.target.value })}
                    rows={6}
                    className="w-full px-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] font-mono leading-relaxed bg-[#fafbfc] focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
                    placeholder={tab === 'prompt' ? '你是一个...' : '技能定义与流程说明'}
                  />
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setForm(null)}
                className="px-4 py-2 border border-[#d9d9d9] bg-white rounded-md text-[13px] text-[#4e5969] hover:border-[#0077ff] hover:text-[#0077ff] transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={!form.name.trim()}
                className="px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}