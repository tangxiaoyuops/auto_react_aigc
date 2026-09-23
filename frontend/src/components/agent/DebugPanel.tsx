import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Eraser,
  Send,
  Bot,
  Bug,
  ChevronDown,
  ScanSearch,
  Wrench,
  CheckCircle2,
  Clock,
  Braces,
  Terminal,
  History,
  MessageSquare,
  XCircle,
} from 'lucide-react';
import { mockReply, nextMsgId, type Step } from '../../utils/mockChat';
import Resizer from '../layout/Resizer';

interface Msg {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  steps?: Step[];
  streaming?: boolean;
}

interface DebugPanelProps {
  agentName: string;
  agentModel: string;
}

export default function DebugPanel({ agentName, agentModel }: DebugPanelProps) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  // 当前在右侧详情面板中查看的执行（对应某条 agent 回复）
  const [activeSteps, setActiveSteps] = useState<{ msgId: number; steps: Step[] } | null>(null);
  // 左侧对话区宽度（px），可拖拽调整，右详情面板自适应
  const [chatWidth, setChatWidth] = useState(320);
  const endRef = useRef<HTMLDivElement>(null);

  const handleChatResize = (delta: number) => {
    setChatWidth((w) => Math.min(520, Math.max(240, w + delta)));
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const reset = useCallback(() => {
    if (sending) return;
    setMessages([]);
    setActiveSteps(null);
  }, [sending]);

  const viewTrace = useCallback(
    (msg: Msg | null) => {
      if (!msg || !msg.steps || msg.steps.length === 0) {
        setActiveSteps(null);
        return;
      }
      setActiveSteps({ msgId: msg.id, steps: msg.steps });
    },
    []
  );

  const send = (e: React.FormEvent) => {
    e.preventDefault();
    const content = input.trim();
    if (!content || sending) return;

    const userMsg: Msg = { id: nextMsgId(), role: 'user', content };
    const botMsgId = nextMsgId();
    const botMsg: Msg = {
      id: botMsgId,
      role: 'assistant',
      content: '',
      streaming: true,
      steps: [
        {
          nodeType: 'THOUGHT',
          nodeName: '任务理解',
          title: '正在解析任务...',
          detail: '正在解析任务...',
          status: 'running',
        },
      ],
    };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput('');
    setSending(true);

    const reply = mockReply(content);
    const steps = reply.steps;
    let stepIndex = 0;

    const timer = setInterval(() => {
      stepIndex += 1;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsgId
            ? {
                ...m,
                steps: steps.slice(0, stepIndex).map((st, i) => ({
                  ...st,
                  status: i < stepIndex - 1 ? ('success' as const) : ('running' as const),
                })),
              }
            : m
        )
      );

      // 执行过程中实时联动详情面板
      const currentSteps = steps.slice(0, stepIndex).map((st, i) => ({
        ...st,
        status: i < stepIndex - 1 ? ('success' as const) : ('running' as const),
      }));
      setActiveSteps({ msgId: botMsgId, steps: currentSteps });

      if (stepIndex >= steps.length) {
        clearInterval(timer);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId ? { ...m, content: reply.content, streaming: false, steps } : m
          )
        );
        setActiveSteps({ msgId: botMsgId, steps });
        setSending(false);
      }
    }, 550);
  };

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* 调试面板头部 */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[#f2f3f5] bg-[#fafbfc] shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-[#38b6ff] to-[#0077ff] text-white flex items-center justify-center">
            <Bug size={14} />
          </div>
          <div>
            <div className="text-[13px] font-medium text-[#1d2129]">对话调试</div>
            <div className="text-[11px] text-[#86909c]">使用当前配置实时测试</div>
          </div>
        </div>
        <button
          onClick={reset}
          disabled={sending}
          className="flex items-center gap-1 px-2.5 py-1.5 text-[12px] text-[#86909c] hover:text-[#4e5969] border border-[#e5e6eb] rounded-md disabled:opacity-50 transition-colors"
        >
          <Eraser size={13} /> 清空
        </button>
      </div>

      {/* 内部双栏：左对话 / 右执行详情（中间可拖拽） */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* 左：对话 */}
        <div style={{ width: `${chatWidth}px` }} className="shrink-0 flex flex-col min-w-[240px]">
          {/* 对话消息区 */}
          <div className="flex-1 overflow-y-auto p-3 bg-[#fafbfc]/60">
            <div className="space-y-3">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full min-h-[220px] text-center">
                  <div className="w-11 h-11 rounded-full bg-[#e8f3ff] text-[#0077ff] flex items-center justify-center mb-3">
                    <Bot size={20} />
                  </div>
                  <p className="text-[13px] text-[#86909c]">开始调试「{agentName}」</p>
                  <p className="text-[11px] text-[#c0c4cc] mt-1.5">模型：{agentModel || '未选择'}</p>
                  <div className="mt-3 flex flex-wrap justify-center gap-1.5">
                    {['分析销售额', '钱怎么花', '总结一下'].map((s) => (
                      <button
                        key={s}
                        onClick={() => setInput(s)}
                        className="px-2.5 py-1 bg-white border border-[#e5e6eb] rounded-full text-[11.5px] text-[#4e5969] hover:border-[#0077ff] hover:text-[#0077ff] transition-colors"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m) =>
                m.role === 'user' ? (
                  <div key={m.id} className="flex justify-end">
                    <div className="bg-[#0077ff] text-white px-3.5 py-2 rounded-lg rounded-br-sm max-w-[85%] whitespace-pre-wrap text-[13px] leading-relaxed shadow-sm">
                      {m.content}
                    </div>
                  </div>
                ) : (
                  <div key={m.id} className="flex justify-start">
                    <div className="max-w-[92%] w-full">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11.5px] font-medium text-[#86909c]">{agentName}</span>
                        {m.streaming && (
                          <span className="flex items-center gap-1 text-[10.5px] text-[#0077ff]">
                            <span className="inline-block w-1.5 h-1.5 bg-[#0077ff] rounded-full animate-pulse" />
                            思考中
                          </span>
                        )}
                      </div>
                      <div
                        className={`bg-white border px-3.5 py-2.5 rounded-lg rounded-tl-sm shadow-sm cursor-pointer transition-colors ${
                          activeSteps?.msgId === m.id
                            ? 'border-[#0077ff] ring-1 ring-[#0077ff]/20'
                            : 'border-[#e8e9ec] hover:border-[#bfd9ff]'
                        }`}
                        onClick={() => viewTrace(m)}
                        title="点击在右侧查看执行详情"
                      >
                        {m.streaming && !m.content ? (
                          <div className="text-[13px] text-[#4e5969]">正在思考并执行任务...</div>
                        ) : (
                          <div className="whitespace-pre-wrap text-[13px] text-[#4e5969] leading-relaxed">
                            {m.content}
                          </div>
                        )}

                        {/* 气泡内仅保留轻量摘要，详细信息在右侧面板 */}
                        {m.steps && m.steps.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-[#f2f3f5] flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <History size={12} className="text-[#0077ff]" />
                              <span className="text-[11px] text-[#86909c]">
                                {m.streaming ? '执行中' : `执行 ${m.steps.length} 步`}
                              </span>
                            </div>
                            {!m.streaming && (
                              <span className="text-[11px] text-[#0077ff] flex items-center gap-0.5">
                                查看详情
                                <ChevronDown size={11} className="rotate-[-90deg]" />
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              )}
              <div ref={endRef} />
            </div>
          </div>

          {/* 输入框 */}
          <form onSubmit={send} className="p-2.5 bg-white border-t border-[#f2f3f5] shrink-0">
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入消息调试当前 Agent..."
                className="flex-1 px-3 py-2 border border-[#d9d9d9] rounded-md text-[12.5px] bg-white focus:outline-none focus:border-[#0077ff] focus:ring-2 focus:ring-[#0077ff]/10 transition-colors"
                disabled={sending}
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="inline-flex items-center gap-1 px-3.5 py-2 bg-[#0077ff] text-white rounded-md text-[12.5px] font-medium hover:bg-[#0066dd] disabled:bg-[#d4d7de] disabled:cursor-not-allowed transition-colors"
              >
                <Send size={13} />
                发送
              </button>
            </div>
          </form>
        </div>

        {/* 拖拽分隔条 */}
        <Resizer onResize={handleChatResize} />

        {/* 右：执行详情 Trace */}
        <div className="flex-1 min-w-[230px] flex flex-col bg-white">
          {/* Trace 头部 */}
          <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#f2f3f5] bg-[#fafbfc] shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-violet-50 text-violet-500 flex items-center justify-center">
                <Terminal size={13} />
              </div>
              <div>
                <div className="text-[12px] font-medium text-[#1d2129]">执行详情</div>
   280|                <div className="text-[10px] text-[#86909c]">Run Trace</div>
              </div>
            </div>
            {activeSteps && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#e8f3ff] text-[#0077ff] text-[10.5px]">
                <span className="w-1 h-1 rounded-full bg-[#0077ff]" />
                {activeSteps.steps.length} 步
              </span>
            )}
          </div>

          {/* Trace 内容 */}
          <div className="flex-1 overflow-y-auto p-3">
            {!activeSteps || activeSteps.steps.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center">
                <div className="w-10 h-10 rounded-full bg-[#f2f3f5] flex items-center justify-center mb-2.5">
                  <MessageSquare size={18} className="text-[#c0c4cc]" />
                </div>
                <p className="text-[12px] text-[#86909c]">暂无执行记录</p>
                <p className="text-[10.5px] text-[#c0c4cc] mt-1">发送消息后，Agent 每一步执行过程将在此展示</p>
              </div>
            ) : (
              <div className="space-y-3">
                {/* 概览卡 */}
                <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#fafbfc] border border-[#f0f1f3]">
                  <div className="flex items-center gap-2">
                    <ScanSearch size={13} className="text-[#0077ff]" />
                    <span className="text-[11.5px] text-[#4e5969]">本轮运行</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-[#86909c]">
                    <span>{agentModel}</span>
                    <span className="w-px h-3 bg-[#e5e6eb]" />
                    <span>
                      总耗时{' '}
                      {(activeSteps.steps.reduce((s, st) => s + (st.duration || 0), 0) / 1000).toFixed(1)}s
                    </span>
                  </div>
                </div>

                {/* 步骤时间线 */}
                <TraceTimeline key={activeSteps.msgId} steps={activeSteps.steps} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const NODE_STYLE: Record<string, { tag: string; icon: React.ReactNode }> = {
  THOUGHT: {
    tag: 'bg-blue-50 text-[#0077ff]',
    icon: <ScanSearch size={13} />,
  },
  TOOL: {
    tag: 'bg-violet-50 text-violet-500',
    icon: <Wrench size={13} />,
  },
  RESULT: {
    tag: 'bg-emerald-50 text-emerald-600',
    icon: <CheckCircle2 size={13} />,
  },
};

function TraceTimeline({ steps }: { steps: Step[] }) {
  const [expanded, setExpanded] = useState<number[]>(steps.map((_, i) => i));

  // 步骤流式递增时，自动展开新增步骤
  useEffect(() => {
    setExpanded((prev) => {
      const missing = steps
        .map((_, i) => i)
        .filter((i) => !prev.includes(i));
      return missing.length ? [...prev, ...missing] : prev;
    });
  }, [steps.length]);

  const toggle = (idx: number) => {
    setExpanded((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  return (
    <div className="space-y-1.5">
      {steps.map((st, idx) => {
        const style = NODE_STYLE[st.nodeType] || NODE_STYLE.THOUGHT;
        const open = expanded.includes(idx);
        const isLast = idx === steps.length - 1;
        const isError = st.status === 'error';

        return (
          <div key={idx} className="relative">
            {/* 时间线竖线 */}
            {!isLast && (
              <span className="absolute left-[11px] top-6 bottom-[-6px] w-px bg-[#e8e9ec]" />
            )}

            <button
              onClick={() => toggle(idx)}
              className={`w-full flex items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors ${
                open ? 'bg-[#f7f9fc]' : 'hover:bg-[#f7f9fc]/60'
              }`}
            >
              {/* 节点图标 */}
              <span
                className={`inline-flex w-[22px] h-[22px] items-center justify-center rounded-full shrink-0 ${
                  st.status === 'running'
                    ? 'border-2 border-[#0077ff] border-t-transparent animate-spin'
                    : isError
                    ? 'bg-red-50 text-red-500'
                    : `${style.tag}`
                }`}
              >
                {st.status === 'running' ? null : isError ? <XCircle size={11} /> : style.icon}
              </span>

              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider shrink-0 ${
                  isError ? 'bg-red-50 text-red-500' : style.tag
                }`}
              >
                {st.nodeType}
              </span>

              <span className="font-medium text-[#4e5969] text-[11.5px] shrink-0">
                {st.nodeName}
              </span>

              <span className="flex-1 truncate text-[11.5px] text-[#c0c4cc]">
                {st.title || st.detail}
              </span>

              {st.duration !== undefined && (
                <span className="flex items-center gap-0.5 text-[10.5px] text-[#c0c4cc] shrink-0">
                  <Clock size={10} />
                  {(st.duration / 1000).toFixed(2)}s
                </span>
              )}

              <ChevronDown
                size={13}
                className={`text-[#c0c4cc] shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
              />
            </button>

            {/* 展开的详细内容 */}
            {open && (
              <div className="ml-[33px] mt-1.5 mb-2 space-y-2">
                {st.detail && (
                  <DetailBlock
                    label={st.nodeType === 'THOUGHT' ? '思考' : '说明'}
                    icon={<ScanSearch size={12} />}
                    text={st.detail}
                  />
                )}

                {st.input && <CodeBlock label="工具输入" text={st.input} />}

                {st.result && <CodeBlock label="工具输出" text={st.result} accent />}

                {st.nodeType === 'RESULT' && st.detail && (
                  <DetailBlock
                    label="最终结果"
                    icon={<CheckCircle2 size={12} />}
                    text={st.detail}
                    green
                  />
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// chat 页复用：轻量执行时间线（内嵌气泡中）
export function StepTimeline({ steps }: { steps: Step[] }) {
  const [expanded, setExpanded] = useState<number[]>(steps.map((_, i) => i));

  useEffect(() => {
    setExpanded((prev) => {
      const missing = steps
        .map((_, i) => i)
        .filter((i) => !prev.includes(i));
      return missing.length ? [...prev, ...missing] : prev;
    });
  }, [steps.length]);

  const toggle = (idx: number) => {
    setExpanded((prev) =>
      prev.includes(idx) ? prev.filter((i) => i !== idx) : [...prev, idx]
    );
  };

  return (
    <div className="mt-3 border-t border-[#f2f3f5] pt-3">
      <div className="text-[11px] font-medium text-[#86909c] tracking-wide mb-2 flex items-center gap-1.5">
        <Terminal size={12} />
        Agent 执行过程
        <span className="text-[#c0c4cc] font-normal">（{steps.length} 步）</span>
      </div>

      <div className="space-y-1.5">
        {steps.map((st, idx) => {
          const style = NODE_STYLE[st.nodeType] || NODE_STYLE.THOUGHT;
          const open = expanded.includes(idx);
          const isLast = idx === steps.length - 1;
          const isError = st.status === 'error';

          return (
            <div key={idx} className="relative">
              {!isLast && (
                <span className="absolute left-[11px] top-6 bottom-[-6px] w-px bg-[#e8e9ec]" />
              )}

              <button
                onClick={() => toggle(idx)}
                className="w-full flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-[#f7f9fc] text-left transition-colors group"
              >
                <span
                  className={`inline-flex w-[22px] h-[22px] items-center justify-center rounded-full shrink-0 ${
                    st.status === 'running'
                      ? 'border-2 border-[#0077ff] border-t-transparent animate-spin'
                      : isError
                      ? 'bg-red-50 text-red-500'
                      : `${style.tag}`
                  }`}
                >
                  {st.status === 'running' ? null : isError ? <XCircle size={11} /> : style.icon}
                </span>

                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider shrink-0 ${
                    isError ? 'bg-red-50 text-red-500' : style.tag
                  }`}
                >
                  {st.nodeType}
                </span>

                <span className="font-medium text-[#4e5969] text-[12px] shrink-0">
                  {st.nodeName}
                </span>

                <span className="flex-1 truncate text-[12px] text-[#c0c4cc]">
                  {st.title || st.detail}
                </span>

                {st.duration !== undefined && (
                  <span className="flex items-center gap-0.5 text-[11px] text-[#c0c4cc] shrink-0">
                    <Clock size={11} />
                    {(st.duration / 1000).toFixed(2)}s
                  </span>
                )}

                <ChevronDown
                  size={14}
                  className={`text-[#c0c4cc] shrink-0 transition-transform ${
                    open ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {open && (
                <div className="ml-[33px] mt-1.5 mb-2 space-y-2">
                  {st.detail && (
                    <DetailBlock label="说明" icon={<ScanSearch size={12} />} text={st.detail} />
                  )}
                  {st.input && <CodeBlock label="工具输入" text={st.input} />}
                  {st.result && <CodeBlock label="工具输出" text={st.result} accent />}
                  {st.nodeType === 'RESULT' && st.detail && (
                    <DetailBlock
                      label="最终结果"
                      icon={<CheckCircle2 size={12} />}
                      text={st.detail}
                      green
                    />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DetailBlock({
  label,
  icon,
  text,
  green,
}: {
  label: string;
  icon?: React.ReactNode;
  text: string;
  green?: boolean;
}) {
  return (
    <div
      className={`px-3 py-2 rounded-md text-[11.5px] leading-relaxed border ${
        green
          ? 'bg-emerald-50/50 border-emerald-100 text-emerald-700'
          : 'bg-[#fafbfc] border-[#f0f1f3] text-[#4e5969]'
      }`}
    >
      <div
        className={`flex items-center gap-1 mb-1 text-[10.5px] font-medium ${
          green ? 'text-emerald-600' : 'text-[#86909c]'
        }`}
      >
        {icon}
        {label}
      </div>
      {text}
    </div>
  );
}

function CodeBlock({ label, text, accent }: { label: string; text: string; accent?: boolean }) {
  return (
    <div
      className={`rounded-md overflow-hidden border ${
        accent ? 'border-violet-200' : 'border-[#e5e6eb]'
      }`}
    >
      <div
        className={`flex items-center gap-1.5 px-3 py-1.5 text-[10.5px] font-medium ${
          accent ? 'bg-violet-50 text-violet-500' : 'bg-[#fafbfc] text-[#86909c]'
        }`}
      >
        {accent ? <Terminal size={11} /> : <Braces size={11} />}
        {label}
      </div>
      <pre
        className={`px-3 py-2 text-[11px] leading-relaxed font-mono whitespace-pre-wrap ${
          accent ? 'text-violet-700 bg-violet-50/30' : 'text-[#4e5969] bg-white'
        }`}
      >
        {text}
      </pre>
    </div>
  );
}