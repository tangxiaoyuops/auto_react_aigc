import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Input, Button, Tag, Alert, App, Tree, message } from 'antd';
import {
  FileText,
  FileCode,
  Save,
  ArrowLeft,
  Plus,
  Folder,
  Play,
  Wand2,
} from 'lucide-react';
import resourcesApi from '../../api/resources';

const { TextArea } = Input;

interface FileNode {
  key: string;
  title: React.ReactNode;
  isLeaf: boolean;
  path?: string;
  children?: FileNode[];
}

export default function SkillEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [skill, setSkill] = useState<any>(null);
  const [files, setFiles] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [activePath, setActivePath] = useState<string>('');
  const [draft, setDraft] = useState<string>('');
  const [runResult, setRunResult] = useState<any>(null);
  const [keyword, setKeyword] = useState('');

  // ===== AI 辅助状态 =====
  const [aiPanelOpen, setAiPanelOpen] = useState(true);
  const [aiAction, setAiAction] = useState<'generate' | 'rewrite'>('generate');
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiError, setAiError] = useState('');
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function init() {
      if (!id) return;
      setLoading(true);
      setNotFound(false);
      try {
        const all = await resourcesApi.list('skill');
        const res = all.find((i: any) => i.id === id);
        setSkill(res || {});
        const fileMap = await resourcesApi.getSkillFiles(id);
        setFiles(fileMap);
        const first = Object.keys(fileMap)[0] || '';
        setActivePath(first);
        setDraft(fileMap[first] ?? '');
      } catch (e: any) {
        if (e?.response?.status === 404) {
          setNotFound(true);
        } else {
          message.error('加载 Skill 失败，请检查后端连接');
        }
      } finally {
        setLoading(false);
      }
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function handleSelect(path: string) {
    if (activePath && draft !== files[activePath]) {
      setFiles((prev) => ({ ...prev, [activePath]: draft }));
    }
    setActivePath(path);
    setDraft(files[path] ?? '');
    setRunResult(null);
  }

  async function persist(next: Record<string, string>) {
    const saved = await resourcesApi.updateSkillFiles(id!, next);
    setFiles(saved);
    setDraft(saved[activePath] ?? '');
    // 从 SKILL.md 同步名称
    const md = saved['SKILL.md'] || '';
    const name = md.match(/^name:\s*(.+)$/m)?.[1]?.trim();
    if (name) setSkill((s: any) => ({ ...(s || {}), name }));
    return saved;
  }

  async function handleSave() {
    if (!activePath) return;
    const next = { ...files, [activePath]: draft };
    setSaving(true);
    try {
      await persist(next);
      message.success('Skill 已保存');
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  }

  async function handleRun() {
    if (!activePath.startsWith('scripts/')) return;
    const next = { ...files, [activePath]: draft };
    setFiles(next);
    try {
      await resourcesApi.updateSkillFiles(id!, next);
    } catch {
      /* 忽略保存错误继续尝试运行 */
    }
    const scriptName = activePath.slice('scripts/'.length);
    setRunning(true);
    setRunResult({ success: false, output: '运行中...' });
    try {
      const r = await resourcesApi.runSkillScript(id!, scriptName);
      setRunResult(r);
    } catch (e: any) {
      setRunResult({ success: false, output: '运行失败: ' + (e?.message || String(e)) });
    } finally {
      setRunning(false);
    }
  }

  function handleAddFile() {
    let i = 1;
    let name = `scripts/task${i}.py`;
    while (files[name]) {
      i++;
      name = `scripts/task${i}.py`;
    }
    const tmpl =
      '"""(技能脚本入口)\n在下方编写可被 Agent 执行的分析脚本。\n"""\nimport json\nimport sys\n\n\ndef main():\n    print(json.dumps({"ok": True}))\n\n\nif __name__ == "__main__":\n    main()\n';
    const next = { ...files, [name]: tmpl };
    setFiles(next);
    setActivePath(name);
    setDraft(tmpl);
    setRunResult(null);
  }

  const isScriptActive = activePath.startsWith('scripts/');

  // ===== 文件树构建（scripts/ 折叠成文件夹） =====
  const treeData = useMemo<FileNode[]>(() => {
    const docs: FileNode[] = [];
    const scriptsChildren: FileNode[] = [];
    const filtered = Object.keys(files)
      .filter((p) => !keyword || p.toLowerCase().includes(keyword.toLowerCase()))
      .sort((a, b) => {
        const aScript = a.startsWith('scripts/');
        const bScript = b.startsWith('scripts/');
        if (aScript !== bScript) return aScript ? 1 : -1;
        return a.localeCompare(b);
      });
    for (const p of filtered) {
      const title = (
        <span className="flex items-center gap-1.5 truncate">
          {p.startsWith('scripts/') ? (
            <FileCode size={13} className="text-amber-500 shrink-0" />
          ) : (
            <FileText size={13} className="text-[#86909c] shrink-0" />
          )}
          <span className="truncate">{p.startsWith('scripts/') ? p.slice('scripts/'.length) : p}</span>
        </span>
      );
      if (p.startsWith('scripts/')) {
        scriptsChildren.push({ key: p, title, isLeaf: true, path: p });
      } else {
        docs.push({ key: p, title, isLeaf: true, path: p });
      }
    }
    if (scriptsChildren.length) {
      docs.unshift({
        key: 'scripts',
        title: (
          <span className="flex items-center gap-1.5 truncate text-[#1d2129] font-medium">
            <Folder size={13} className="text-[#4e5969] shrink-0" />
            <span>scripts</span>
          </span>
        ),
        isLeaf: false,
        children: scriptsChildren,
      });
    }
    return docs;
  }, [files, keyword]);

  // ===== AI 辅助逻辑 =====
  function applyAiFiles(genFiles: Record<string, string>) {
    setFiles((prev) => ({ ...prev, ...genFiles }));
    const nextActive = genFiles[activePath] ? activePath : Object.keys(genFiles)[0] || '';
    if (nextActive) {
      setActivePath(nextActive);
      setDraft(genFiles[nextActive] ?? '');
    }
    const md = genFiles['SKILL.md'] || '';
    const nm = md.match(/^name:\s*(.+)$/m)?.[1]?.trim();
    if (nm) setSkill((s: any) => ({ ...(s || {}), name: nm }));
    setRunResult(null);
  }

  async function handleAiGenerate() {
    const desc = aiPrompt.trim();
    if (!desc) {
      message.warning('请先描述你想要生成的 Skill 需求');
      return;
    }
    setAiGenerating(true);
    setAiError('');
    try {
      const res = await resourcesApi.assistSkill({
        action: 'generate',
        description: desc,
        name_hint: skill?.name || 'custom-skill',
      });
      applyAiFiles(res.files || {});
      message.success('AI 已生成，请点击「保存」落盘');
    } catch (e: any) {
      setAiError(e?.message || 'AI 生成失败');
    } finally {
      setAiGenerating(false);
    }
  }

  async function handleAiRewrite() {
    const desc = aiPrompt.trim();
    if (!desc) {
      message.warning('请描述你的改写要求');
      return;
    }
    setAiGenerating(true);
    setAiError('');
    try {
      const res = await resourcesApi.assistSkill({
        action: 'rewrite',
        description: desc,
        current_files: { ...files },
        target: activePath || 'all',
        name_hint: skill?.name || 'custom-skill',
      });
      applyAiFiles(res.files || {});
      message.success('AI 已完成改写，请点击「保存」落盘');
    } catch (e: any) {
      setAiError(e?.message || '改写失败');
    } finally {
      setAiGenerating(false);
    }
  }

  async function handleAiEditCurrent() {
    // 工具条快捷入口：直接改写当前文件（无需用户先输入描述）
    setAiAction('rewrite');
    const desc = `改写并完善当前文件 ${activePath}，使其更专业、可直接运行`;
    setAiGenerating(true);
    setAiError('');
    try {
      const res = await resourcesApi.assistSkill({
        action: 'rewrite',
        description: desc,
        current_files: { ...files },
        target: activePath || 'all',
        name_hint: skill?.name || 'custom-skill',
      });
      applyAiFiles(res.files || {});
      message.success('AI 已完成改写，请点击「保存」落盘');
    } catch (e: any) {
      setAiError(e?.message || '改写失败');
    } finally {
      setAiGenerating(false);
    }
  }

  return (
    <App>
      <div style={{ height: 'calc(100vh - 60px)' }}>
        {/* 顶栏 */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#e5e6eb] bg-white">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => navigate('/resources')}
              className="w-8 h-8 flex items-center justify-center rounded-md hover:bg-[#f0f1f3] text-[#4e5969]"
              title="返回"
            >
              <ArrowLeft size={18} />
            </button>
            <div className="min-w-0">
              <div className="text-[15px] font-semibold text-[#1d2129] truncate">
                {notFound ? 'Skill 未找到' : skill?.name || 'Skill'}
              </div>
              <div className="text-[12px] text-[#86909c] truncate">{skill?.description || ''}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button icon={<Plus size={14} />} onClick={handleAddFile}>
              新增脚本
            </Button>
            <Button type="primary" icon={<Save size={14} />} loading={saving} onClick={handleSave}>
              保存
            </Button>
          </div>
        </div>

        {/* 主区 */}
        <div className="flex" style={{ height: 'calc(100% - 57px)' }}>
          {/* 左：文件树 */}
          <div className="w-60 border-r border-[#e5e6eb] bg-[#fafbfc] flex flex-col">
            <div className="px-3 pt-3 pb-2 flex items-center gap-1.5 text-[13px] font-semibold text-[#1d2129]">
              <Folder size={14} /> 文件
            </div>
            <div className="px-3 pb-2">
              <Input
                size="small"
                placeholder="筛选文件"
                allowClear
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
              />
            </div>
            <div className="flex-1 overflow-y-auto px-1.5 pb-3">
              {loading ? (
                <div className="text-[12px] text-[#c0c4cc] text-center py-8">加载中...</div>
              ) : treeData.length === 0 ? (
                <div className="text-[12px] text-[#c0c4cc] text-center py-8">暂无文件，点击「新增脚本」</div>
              ) : (
                <Tree
                  className="skill-file-tree"
                  treeData={treeData}
                  defaultExpandAll
                  showIcon={false}
                  blockNode
                  selectedKeys={activePath ? [activePath] : []}
                  onSelect={(keys: any[]) => {
                    const k = keys[0];
                    if (k && k !== 'scripts') handleSelect(String(k));
                  }}
                  titleRender={(node: any) => (
                    <span className="text-[14px] leading-7">{node.title}</span>
                  )}
                />
              )}
            </div>
          </div>

          {/* 中：编辑区 */}
          <div className="flex-1 min-w-0 flex flex-col bg-white">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[#f2f3f5]">
              <span className="text-[13px] font-mono text-[#1d2129] truncate">{activePath || '（选择左侧文件）'}</span>
              <Tag color={isScriptActive ? 'orange' : 'default'}>{isScriptActive ? '可执行脚本' : '文档'}</Tag>
              <div className="flex-1" />
              <Button
                size="small"
                icon={<Wand2 size={13} />}
                disabled={!activePath || aiGenerating}
                onClick={handleAiEditCurrent}
              >
                AI 改写当前文件
              </Button>
            </div>
            {activePath ? (
              <div className="flex-1 flex flex-col min-h-0">
                <div className="flex-1 min-h-0">
                  <TextArea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    spellCheck={false}
                    autoSize={false}
                    className="h-full w-full resize-none border-0 font-mono text-[13px] leading-relaxed py-3 px-4 focus:shadow-none"
                  />
                </div>
                <div className="flex items-center justify-between px-4 py-2 border-t border-[#f2f3f5] shrink-0">
                  <span className="text-[12px] text-[#86909c]">
                    {isScriptActive ? '脚本可被 Agent 通过 run_skill_script 工具执行' : '文本会装载进 Agent 上下文'}
                  </span>
                  {isScriptActive && (
                    <Button size="small" type="primary" ghost icon={<Play size={13} />} loading={running} onClick={handleRun}>
                      运行
                    </Button>
                  )}
                </div>
                {runResult && (
                  <div className="px-4 pb-3 shrink-0">
                    <Alert
                      type={runResult.success ? 'success' : 'error'}
                      message={runResult.success ? '执行成功' : '执行失败'}
                      description={
                        <pre className="m-0 whitespace-pre-wrap font-mono text-[12px] max-h-44 overflow-auto">
                          {runResult.output || runResult.error || ''}
                        </pre>
                      }
                      showIcon
                    />
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-[#c0c4cc]">
                从左侧文件树选择一个文件开始编辑
              </div>
            )}
          </div>

          {/* 右：AI 辅助面板 */}
          {aiPanelOpen ? (
            <div className="w-72 border-l border-[#e5e6eb] bg-[#fcfdff] flex flex-col">
              <div className="flex items-center justify-between px-4 py-3 border-b border-[#f2f3f5]">
                <div className="flex items-center gap-1.5 text-[13px] font-semibold text-[#7c3aed]">
                  <Wand2 size={14} /> AI 辅助
                </div>
                <Button type="text" size="small" onClick={() => setAiPanelOpen(false)}>
                  收起
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
                <div className="flex flex-col gap-1.5">
                  <span className="text-[12px] text-[#86909c]">操作</span>
                  <div className="flex gap-1">
                    <Button
                      size="small"
                      type={aiAction === 'generate' ? 'primary' : 'default'}
                      onClick={() => setAiAction('generate')}
                    >
                      生成全套
                    </Button>
                    <Button
                      size="small"
                      type={aiAction === 'rewrite' ? 'primary' : 'default'}
                      onClick={() => setAiAction('rewrite')}
                    >
                      改写/续写
                    </Button>
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[12px] text-[#86909c]">
                    {aiAction === 'generate' ? '需求描述（说明要生成的 Skill 用途）' : '改写要求（说明想怎么改）'}
                  </span>
                  <TextArea
                    rows={5}
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="例：计算员工离职率统计分析，支持按部门筛选，输出分析脚本与字段说明"
                  />
                </div>
                <Button
                  type="primary"
                  block
                  loading={aiGenerating}
                  icon={<Wand2 size={14} />}
                  onClick={aiAction === 'generate' ? handleAiGenerate : handleAiRewrite}
                >
                  {aiGenerating ? 'AI 生成中...' : aiAction === 'generate' ? 'AI 生成 Skill' : 'AI 改写'}
                </Button>
                <p className="text-[11px] leading-5 text-[#86909c] m-0">
                  生成/改写结果会合并到左侧文件树中（含 SKILL.md、scripts/*.py 等），确认后点击顶部「保存」落盘生效。
                </p>
                {aiError && <Alert type="error" message={aiError} showIcon closable={false} />}
              </div>
            </div>
          ) : (
            <div
              className="w-9 border-l border-[#e5e6eb] bg-[#fafbfc] flex items-center justify-center cursor-pointer text-[#7c3aed] hover:bg-[#f3f4ff]"
              onClick={() => setAiPanelOpen(true)}
              title="打开 AI 辅助"
            >
              <Wand2 size={16} />
            </div>
          )}
        </div>
      </div>
    </App>
  );
}
