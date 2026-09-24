import React, { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bot, Eraser } from 'lucide-react';
import { useAgentStore } from '../../stores/agentStore';
import { mockReply, nextMsgId, type Step } from '../../utils/mockChat';
import { StepTimeline } from '../../components/agent/DebugPanel';
import Markdown from '../../components/Markdown';
import { ensureSession, startRun, streamRun } from '../../api/chat';

interface Msg {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  steps?: Step[];
  streaming?: boolean;
}

export default function Chat() {
  const [params] = useSearchParams();
  const agents = useAgentStore((s) => s.agents);
  const agentId = params.get('agent');
  const [selectedAgentId, setSelectedAgentId] = useState<string>(
    agentId || agents[0]?.id || ''
  );

  const currentAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  // 切换 Agent 时清空对话
  useEffect(() => {
    setMessages([]);
  }, [selectedAgentId]);

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (e: React.FormEvent) => {
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
      steps: [{ nodeType: 'THOUGHT', nodeName: '任务理解', title: '正在解析任务...', detail: '正在解析任务...', status: 'running' }],
    };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput('');
    setSending(true);

    // 尝试走后端 SSE；仅当"无法建立后端连接"时回退到 mock（离线演示）
    const steps: Step[] = [];
    let finalContent = '';

    try {
      const sessionId = await ensureSession(currentAgent?.model);
      await startRun(sessionId, content);

      // 单个消息内聚合并实时更新 steps
      const updateSteps = (newSteps: Step[]) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === botMsgId ? { ...m, steps: newSteps, content: finalContent } : m))
        );
      };

      const appendStep = (step: Step) => {
        const last = steps[steps.length - 1];
        if (last && last.status === 'running' && step.status === 'running') {
          steps[steps.length - 1] = step;
        } else {
          steps.push(step);
        }
        updateSteps([...steps]);
      };

      await streamRun(sessionId, (type, step) => {
        if (type === 'run_start') return;
        if (type === 'thought') {
          appendStep({ nodeType: 'THOUGHT', nodeName: step.nodeName || '思考', title: step.title || '思考', detail: step.detail || '', status: 'success' });
        } else if (type === 'tool_call_start') {
          appendStep({ nodeType: 'TOOL', nodeName: step.nodeName || step.title || '工具', title: `调用 ${step.nodeName || step.title || '工具'}`, input: step.input || '', status: 'running' });
        } else if (type === 'tool_call_end') {
          appendStep({ nodeType: 'TOOL', nodeName: step.nodeName || '工具', title: `${step.nodeName || '工具'} 完成`, result: step.result || '', duration: step.duration, status: 'success' });
        } else if (type === 'result') {
          finalContent = step.detail || step.title || '';
          appendStep({ nodeType: 'RESULT', nodeName: step.nodeName || '结果', title: step.title || '完成', detail: step.detail || '', status: 'success' });
        } else if (type === 'error') {
          appendStep({ nodeType: 'ERROR', nodeName: '错误', title: step.title || '执行出错', detail: step.detail || '', status: 'error' });
        }
      });
    } catch (err) {
      // 后端连接失败，回退 mock（模拟执行链路）
      const reply = mockReply(content);
      const msteps = reply.steps;
      let i = 0;
      const timer = setInterval(() => {
        i += 1;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsgId
              ? {
                  ...m,
                  steps: msteps.slice(0, i).map((st, idx) => ({
                    ...st,
                    status: idx < i - 1 ? ('success' as const) : ('running' as const),
                  })),
                }
              : m
          )
        );
        if (i >= msteps.length) {
          clearInterval(timer);
          setMessages((prev) =>
            prev.map((m) => (m.id === botMsgId ? { ...m, content: reply.content, streaming: false, steps: msteps } : m))
          );
          setSending(false);
        }
      }, 550);
      return;
    }

    // 后端路径收尾
    await new Promise((r) => setTimeout(r, 200));
    setMessages((prev) =>
      prev.map((m) =>
        m.id === botMsgId ? { ...m, content: finalContent || m.content, streaming: false, steps: steps.length ? steps : m.steps } : m
      )
    );
    setSending(false);
  };

  return (
    <div className="h-full flex">
      {/* 左侧 Agent 列表 */}
      <div className="w-56 bg-white border-r border-[#e5e6eb] flex flex-col shrink-0">
        <div className="h-12 flex items-center justify-between px-4 border-b border-[#f2f3f5]">
          <span className="text-[13px] font-medium text-gray-700">Agent 列表</span>
          <Bot size={16} className="text-gray-300" />
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgentId(agent.id)}
              className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-[13px] transition-colors border-r-2 ${
                selectedAgentId === agent.id
                  ? 'bg-[#e8f3ff] border-[#0077ff] text-[#0077ff] font-medium'
                  : 'border-transparent text-gray-600 hover:bg-gray-50'
              }`}
            >
              <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                {agent.name.slice(0, 1)}
              </div>
              <span className="truncate">{agent.name}</span>
            </button>
          ))}
          {agents.length === 0 && (
            <div className="px-4 py-6 text-[12px] text-gray-400 text-center">暂无Agent</div>
          )}
        </div>
      </div>

      {/* 右侧对话区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶栏 */}
        <div className="bg-white border-b border-[#e5e6eb] px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center text-xs font-bold">
              {currentAgent?.name.slice(0, 1) || 'A'}
            </div>
            <div>
              <div className="text-[14px] font-medium text-gray-800">
                {currentAgent?.name || '未选择Agent'}
              </div>
              <div className="text-[11px] text-gray-400">
                {currentAgent?.model || ''} · {currentAgent?.status === 'published' ? '已上架' : '未上架'}
              </div>
            </div>
          </div>
          <button
            onClick={() => setMessages([])}
            className="flex items-center gap-1 px-3 py-1.5 text-[12px] text-gray-400 hover:text-gray-600 border border-gray-200 rounded"
          >
            <Eraser size={14} /> 清空对话
          </button>
        </div>

        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 py-16">
                <div className="text-4xl mb-3">🤖</div>
                <p className="text-[14px]">开始调试「{currentAgent?.name || 'Agent'}」</p>
                <p className="text-[12px] mt-1">试试输入「分析销售额」或「总结一下」</p>
              </div>
            )}

            {messages.map((m) =>
              m.role === 'user' ? (
                <div key={m.id} className="flex justify-end">
                  <div className="bg-[#0077ff] text-white px-4 py-2.5 rounded-lg max-w-[80%] whitespace-pre-wrap text-[13px] leading-relaxed">
                    {m.content}
                  </div>
                </div>
              ) : (
                <div key={m.id} className="flex justify-start">
                  <div className="max-w-[85%] w-full min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[12px] font-medium text-gray-500">
                        {currentAgent?.name || 'Agent'}
                      </span>
                    </div>
                    <div className="bg-white border border-[#e5e6eb] px-4 py-3 rounded-lg">
                      {m.streaming && !m.content ? (
                        <div className="flex items-center gap-2 text-gray-400 text-[13px]">
                          <span className="inline-block w-2 h-2 bg-[#0077ff] rounded-full animate-pulse" />
                          正在思考中...
                        </div>
                      ) : (
                        <Markdown content={m.content} className="whitespace-pre-wrap" />
                      )}

                      {m.steps && m.steps.length > 0 && (
                        <StepTimeline steps={m.steps} />
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
        <form onSubmit={send} className="p-4 bg-white border-t border-[#e5e6eb] shrink-0">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="输入消息，试试「分析销售额」或「总结一下」..."
              className="flex-1 p-2.5 border border-gray-200 rounded-md text-[13px] focus:outline-none focus:border-[#0077ff]"
              disabled={sending}
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="px-6 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {sending ? '处理中...' : '发送'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}