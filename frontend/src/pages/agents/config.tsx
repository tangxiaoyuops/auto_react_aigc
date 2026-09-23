import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Trash2,
  Check,
  Rocket,
  Settings2,
  Bot,
  FileText,
  Sparkles,
  Network,
  Wand2,
} from 'lucide-react';
import { useAgentStore, createNewAgent } from '../../stores/agentStore';
import {
  MODEL_OPTIONS,
  type Agent,
  type AgentCapabilities,
  type AgentKnowledge,
  type AgentOntology,
  type AgentSkill,
} from '../../types/agent';
import { KNOWLEDGE_POOL, ONTOLOGY_POOL, SKILL_POOL } from '../../mock/agents';
import DebugPanel from '../../components/agent/DebugPanel';
import Resizer from '../../components/layout/Resizer';

export default function AgentConfig() {
  const { id } = useParams();
  const navigate = useNavigate();
  const agents = useAgentStore((s) => s.agents);
  const updateAgent = useAgentStore((s) => s.updateAgent);
  const addAgent = useAgentStore((s) => s.addAgent);
  const publishAgent = useAgentStore((s) => s.publishAgent);

  // 新建时无 id
  const isNew = !id;
  const [saved, setSaved] = useState(false);
  // 左配置栏宽度（px），可拖拽调整
  const [leftWidth, setLeftWidth] = useState(640);

  const handleLeftResize = (delta: number) => {
    setLeftWidth((w) => Math.min(820, Math.max(400, w + delta)));
  };

  // 本地编辑状态
  const [form, setForm] = useState<Agent | null>(() => {
    if (isNew) return createNewAgent();
    const found = agents.find((a) => a.id === id);
    return found ? { ...found, capabilities: JSON.parse(JSON.stringify(found.capabilities)) } : null;
  });

  if (!form) {
    return (
      <div className="p-8 text-gray-500">
        Agent 不存在。{' '}
        <button className="text-blue-600" onClick={() => navigate('/agents')}>
          返回列表
        </button>
      </div>
    );
  }

  const setField = <K extends keyof Agent>(key: K, value: Agent[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const setCap = (key: keyof AgentCapabilities, value: any) => {
    setForm((prev) =>
      prev ? { ...prev, capabilities: { ...prev.capabilities, [key]: value } } : prev
    );
  };

  const handleSave = () => {
    if (isNew) {
      addAgent(form);
      navigate(`/agents/${form.id}`);
    } else {
      updateAgent(form.id, form);
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    }
  };

  const handlePublish = () => {
    if (isNew) {
      addAgent({ ...form, status: 'published' });
      navigate(`/agents/${form.id}`);
    } else {
      publishAgent(form.id);
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    }
  };

  // 能力操作
  const addKnowledge = (kb: AgentKnowledge) => {
    if (form.capabilities.knowledgeBases.some((k) => k.id === kb.id)) return;
    setCap('knowledgeBases', [...form.capabilities.knowledgeBases, kb]);
  };
  const removeKnowledge = (id: string) =>
    setCap('knowledgeBases', form.capabilities.knowledgeBases.filter((k) => k.id !== id));

  const addOntology = (on: AgentOntology) => {
    if (form.capabilities.ontologies.some((o) => o.id === on.id)) return;
    setCap('ontologies', [...form.capabilities.ontologies, on]);
  };
  const removeOntology = (id: string) =>
    setCap('ontologies', form.capabilities.ontologies.filter((o) => o.id !== id));

  const addSkill = (sk: AgentSkill) => {
    if (form.capabilities.skills.some((s) => s.id === sk.id)) return;
    setCap('skills', [...form.capabilities.skills, sk]);
  };
  const removeSkill = (id: string) =>
    setCap('skills', form.capabilities.skills.filter((s) => s.id !== id));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-[#f0f1f3] text-[#4e5969] transition-colors"
            title="返回"
          >
            <ArrowLeft size={18} />
          </button>
          <h1 className="text-[17px] font-semibold text-[#1d2129]">{form.name}</h1>
          <span className="text-[12px] text-[#c0c4cc]">ID: {form.id}</span>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[12px] ${
            form.status === 'published'
              ? 'bg-emerald-50 text-emerald-600'
              : 'bg-orange-50 text-orange-600'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              form.status === 'published' ? 'bg-emerald-500' : 'bg-orange-400'
            }`} />
            {form.status === 'published' ? '已上架' : '未上架'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {saved && (
            <span className="text-[13px] text-emerald-600 flex items-center gap-1">
              <Check size={14} /> 已保存
            </span>
          )}
          <button
            onClick={handleSave}
            className="inline-flex items-center px-4 py-1.5 border border-[#d9d9d9] bg-white rounded-md text-[13px] text-[#4e5969] hover:border-[#0077ff] hover:text-[#0077ff] transition-colors"
          >
            保存
          </button>
          <button
            onClick={handlePublish}
            className="inline-flex items-center gap-1 px-4 py-1.5 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
          >
            <Rocket size={14} />
            {form.status === 'published' ? '已上架' : '上架'}
          </button>
        </div>
      </div>

      {/* 双栏：左配置 + 右调试（中间可拖拽调整） */}
      <div className="flex items-start">
        {/* 左栏：配置 */}
        <div style={{ width: `${leftWidth}px` }} className="shrink-0">
          <div className="space-y-5">
          {/* 基础配置 */}
          <div className="panel overflow-hidden">
            <div className="px-6 pt-5 pb-3 border-b border-[#f2f3f5]">
              <div className="flex items-center gap-2 text-[15px] font-medium text-[#1d2129] mb-4">
                <Settings2 size={16} className="text-[#0077ff]" />
                基础配置
              </div>

              <div className="mb-2 text-[13px] text-[#4e5969]">
                <span className="text-red-500 mr-0.5">*</span>模型
              </div>
              <div className="relative inline-block w-72">
                <select
                  value={form.model}
                  onChange={(e) => setField('model', e.target.value)}
                  className="w-full px-3 py-2 border border-[#d9d9d9] rounded-md text-[13px] bg-white focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors appearance-none pr-9"
                >
                  {MODEL_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[#86909c] pointer-events-none text-[11px]">▾</span>
              </div>
              <div className="text-[12px] text-[#c0c4cc] mt-2">选择 Agent 使用的底层大模型，不同模型的能力与成本有所不同</div>
            </div>

            {/* 提示词 */}
            <div className="px-6 py-5 border-b border-[#f2f3f5]">
              <div className="flex items-center gap-2 text-[15px] font-medium text-[#1d2129] mb-3">
                <FileText size={16} className="text-[#0077ff]" />
                提示词
              </div>
              <div className="text-[12px] text-[#86909c] mb-2">系统提示词 / System Prompt</div>
              <textarea
                value={form.systemPrompt}
                onChange={(e) => setField('systemPrompt', e.target.value)}
                rows={8}
                className="w-full px-3.5 py-2.5 border border-[#d9d9d9] rounded-md text-[13px] font-mono text-[#4e5969] focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors leading-relaxed bg-[#fafbfc]"
              />
              <div className="text-[12px] text-[#c0c4cc] mt-2">
                💡 系统提示词定义了 Agent 的角色定位与行为准则，将随每次对话发送给模型
              </div>
            </div>

            {/* 能力 */}
            <div className="px-6 py-5">
              <div className="flex items-center gap-2 text-[15px] font-medium text-[#1d2129] mb-3">
                <Sparkles size={16} className="text-[#0077ff]" />
                能力
              </div>
              <div className="text-[12px] text-[#c0c4cc] mb-5">
                为 Agent 挂载知识库、本体与 Skill，增强其专业能力
              </div>

              <div className="space-y-5">
                <CapabilitySection
                  icon={<Bot size={15} />}
                  iconCls="bg-blue-50 text-[#0077ff]"
                  title="知识库"
                  desc="选择业务知识，Agent可结合意图识别能力对知识相关问题进行回复"
                  selected={form.capabilities.knowledgeBases}
                  pool={KNOWLEDGE_POOL}
                  onAdd={addKnowledge}
                  onRemove={removeKnowledge}
                />

                <CapabilitySection
                  icon={<Network size={15} />}
                  iconCls="bg-violet-50 text-violet-500"
                  title="本体"
                  desc="Agent可通过大模型读取本体语义，对相关问题进行回复及动作执行，支持添加一个本体"
                  selected={form.capabilities.ontologies}
                  pool={ONTOLOGY_POOL}
                  onAdd={addOntology}
                  onRemove={removeOntology}
                />

                <CapabilitySection
                  icon={<Wand2 size={15} />}
                  iconCls="bg-amber-50 text-amber-500"
                  title="Skill"
                  desc="为Agent加载设计好的知识和流程，让Agent具备特定领域的专业能力"
                  selected={form.capabilities.skills}
                  pool={SKILL_POOL}
                  onAdd={addSkill}
                  onRemove={removeSkill}
                />
              </div>
            </div>
          </div>
        </div>
        </div>

        {/* 拖拽分隔条 */}
        <Resizer onResize={handleLeftResize} className="self-stretch mt-[168px]" />

        {/* 右栏：对话调试（剩余空间自适应） */}
        <div className="flex-1 min-w-0 lg:sticky lg:top-6">
          <div className="panel overflow-hidden h-[calc(100vh-150px)] min-h-[500px]">
            <DebugPanel agentName={form.name} agentModel={form.model} />
          </div>
        </div>
      </div>
    </div>
  );
}

interface CapabilitySectionProps {
  icon: React.ReactNode;
  iconCls: string;
  title: string;
  desc: string;
  selected: any[];
  pool: { id: string; name: string; description: string }[];
  onAdd: (item: any) => void;
  onRemove: (id: string) => void;
}

function CapabilitySection({
  icon,
  iconCls,
  title,
  desc,
  selected,
  pool,
  onAdd,
  onRemove,
}: CapabilitySectionProps) {
  const [showPicker, setShowPicker] = useState(false);

  return (
    <div className="border border-[#e8e9ec] rounded-lg p-4 hover:border-[#d0d5dd] transition-colors bg-white shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${iconCls}`}>
            {icon}
          </div>
          <div>
            <div className="text-[14px] font-medium text-[#1d2129]">{title}</div>
            <div className="text-[12px] text-[#86909c] mt-0.5 leading-relaxed max-w-md">{desc}</div>
          </div>
        </div>
        <button
          onClick={() => setShowPicker((v) => !v)}
          className="flex items-center gap-1 px-3 py-1.5 border border-[#0077ff] text-[#0077ff] rounded-md text-[12px] hover:bg-[#e8f3ff] transition-colors shrink-0"
        >
          <Plus size={14} /> 添加
        </button>
      </div>

      {selected.length > 0 ? (
        <ul className="mt-3 space-y-2">
          {selected.map((item: any) => (
            <li
              key={item.id}
              className="flex items-center justify-between px-3 py-2 rounded bg-[#f7f8fa] border border-[#f0f1f3]"
            >
              <div>
                <div className="text-[13px] text-gray-700">{item.name}</div>
                <div className="text-[12px] text-gray-400">{item.description}</div>
              </div>
              <button
                onClick={() => onRemove(item.id)}
                className="text-gray-300 hover:text-red-500"
              >
                <Trash2 size={15} />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-3 text-[12px] text-gray-300 py-2">未添加，点击「添加」选择</div>
      )}

      {showPicker && (
        <div className="mt-3 border border-[#e5e6eb] rounded p-2 max-h-48 overflow-y-auto">
          {pool.map((item) => {
            const inSelected = selected.some((s: any) => s.id === item.id);
            return (
              <button
                key={item.id}
                disabled={inSelected}
                onClick={() => onAdd(item)}
                className="w-full flex items-center justify-between px-3 py-2 rounded hover:bg-[#f7f8fa] text-left disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div>
                  <div className="text-[13px] text-gray-700">{item.name}</div>
                  <div className="text-[12px] text-gray-400">{item.description}</div>
                </div>
                {inSelected ? (
                  <Check size={15} className="text-green-500" />
                ) : (
                  <Plus size={15} className="text-gray-300" />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}