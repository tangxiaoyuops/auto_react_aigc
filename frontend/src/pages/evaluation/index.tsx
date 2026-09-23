import { useState } from 'react';
import { Play, BarChart3, ClipboardCheck, ListChecks, Target, TrendingUp } from 'lucide-react';

interface EvalCase {
  id: string;
  question: string;
  expected: string;
  actual: string;
  score: number;
  status: 'passed' | 'failed';
}

interface EvalTask {
  id: string;
  name: string;
  agentName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  totalCases: number;
  passedCases: number;
  createdAt: string;
}

const SEED_TASKS: EvalTask[] = [
  {
    id: 't1',
    name: '客服助手回归评测',
    agentName: '客服助手',
    status: 'completed',
    progress: 100,
    totalCases: 20,
    passedCases: 18,
    createdAt: '2026-09-20 15:30',
  },
  {
    id: 't2',
    name: '法规问答能力评测',
    agentName: 'LegalRegulatoryDashboard_1',
    status: 'running',
    progress: 56,
    totalCases: 35,
    passedCases: 19,
    createdAt: '2026-09-22 09:12',
  },
  {
    id: 't3',
    name: '研报生成质量评测',
    agentName: '智能研报Agent',
    status: 'completed',
    progress: 100,
    totalCases: 12,
    passedCases: 9,
    createdAt: '2026-09-18 17:45',
  },
];

export default function Evaluation() {
  const [tasks] = useState<EvalTask[]>(SEED_TASKS);
  const [tab, setTab] = useState<'tasks' | 'datasets'>('tasks');
  const [selectedTask, setSelectedTask] = useState<EvalTask | null>(null);
  const [caseList] = useState<EvalCase[]>([
    { id: 'c1', question: '2026年北京社保缴费基数上限是多少？', expected: '35283元', actual: '35283元', score: 1, status: 'passed' },
    { id: 'c2', question: '公积金提取需要哪些材料？', expected: '身份证、购房合同...', actual: '身份证、工作证明...', score: 0.6, status: 'failed' },
    { id: 'c3', question: '个税专项附加扣除有哪些项目？', expected: '子女教育、住房贷款...', actual: '子女教育、住房贷款...', score: 1, status: 'passed' },
  ]);

  const statusLabel: Record<EvalTask['status'], string> = {
    pending: '待执行',
    running: '评测中',
    completed: '已完成',
    failed: '失败',
  };

  const statusStyle: Record<EvalTask['status'], { cls: string; dot: string }> = {
    pending: { cls: 'bg-gray-50 text-gray-500', dot: 'bg-gray-400' },
    running: { cls: 'bg-blue-50 text-[#0077ff]', dot: 'bg-[#0077ff] animate-pulse' },
    completed: { cls: 'bg-emerald-50 text-emerald-600', dot: 'bg-emerald-500' },
    failed: { cls: 'bg-red-50 text-red-500', dot: 'bg-red-500' },
  };

  const completedTasks = tasks.filter((t) => t.status === 'completed');
  const avgPassRate = completedTasks.length
    ? Math.round(
        completedTasks.reduce((s, t) => s + t.passedCases / t.totalCases, 0) / completedTasks.length * 100
      )
    : 0;

  return (
    <div className="p-6">
      {/* 页头 */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[20px] font-semibold text-[#1d2129]">Agent评测</h1>
          <p className="text-[13px] text-[#86909c] mt-1">通过标准化用例集持续验证 Agent 的能力与质量</p>
        </div>
        <button
          onClick={() => setTab('tasks')}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#0077ff] text-white rounded-md text-[13px] font-medium hover:bg-[#0066dd] transition-colors shadow-sm shadow-[#0077ff]/20"
        >
          <Play size={16} /> 新建评测
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        <div className="panel p-4 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-blue-50 text-[#0077ff] flex items-center justify-center">
            <ListChecks size={18} />
          </div>
          <div>
            <div className="text-[26px] font-semibold text-[#1d2129] leading-tight">{tasks.length}</div>
            <div className="text-[12px] text-[#86909c]">评测任务</div>
          </div>
        </div>
        <div className="panel p-4 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-500 flex items-center justify-center">
            <TrendingUp size={18} />
          </div>
          <div>
            <div className="text-[26px] font-semibold text-[#1d2129] leading-tight">{avgPassRate}%</div>
            <div className="text-[12px] text-[#86909c]">平均通过率</div>
          </div>
        </div>
        <div className="panel p-4 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-violet-50 text-violet-500 flex items-center justify-center">
            <Target size={18} />
          </div>
          <div>
            <div className="text-[26px] font-semibold text-[#1d2129] leading-tight">
              {tasks.reduce((s, t) => s + t.totalCases, 0)}
            </div>
            <div className="text-[12px] text-[#86909c]">评测用例数</div>
          </div>
        </div>
      </div>

      {/* 子Tab */}
      <div className="flex gap-6 border-b border-[#e5e6eb] mb-4">
        {[
          { key: 'tasks' as const, label: '评测任务', icon: <ListChecks size={15} /> },
          { key: 'datasets' as const, label: '评测集管理', icon: <ClipboardCheck size={15} /> },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
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

      {tab === 'tasks' ? (
        <div className="panel overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left bg-[#fafbfc] border-b border-[#f0f1f3]">
                <th className="py-3 px-5 font-medium text-[#86909c]">任务名称</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">Agent</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">状态</th>
                <th className="py-3 px-4 font-medium text-[#86909c] w-52">进度</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">通过率</th>
                <th className="py-3 px-4 font-medium text-[#86909c]">创建时间</th>
                <th className="py-3 px-5 font-medium text-[#86909c] text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => {
                const st = statusStyle[task.status];
                const passRate = task.status === 'completed'
                  ? Math.round((task.passedCases / task.totalCases) * 100)
                  : null;
                return (
                  <tr key={task.id} className="border-b border-[#f5f6f8] hover:bg-[#f7f9fc] transition-colors">
                    <td className="py-4 px-5">
                      <button
                        onClick={() => setSelectedTask(task)}
                        className="flex items-center gap-2 font-medium text-[#1d2129] hover:text-[#0077ff]"
                      >
                        <BarChart3 size={15} className="text-[#0077ff]/50" />
                        {task.name}
                      </button>
                    </td>
                    <td className="py-4 px-4 text-[#4e5969]">{task.agentName}</td>
                    <td className="py-4 px-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[12px] ${st.cls}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
                        {statusLabel[task.status]}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-28 h-1.5 bg-[#f0f1f3] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              task.status === 'failed'
                                ? 'bg-red-400'
                                : task.status === 'completed'
                                ? 'bg-emerald-400'
                                : 'bg-[#0077ff]'
                            }`}
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                        <span className="text-[12px] text-[#86909c] w-9">{task.progress}%</span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      {passRate !== null ? (
                        <span className={`font-medium ${passRate >= 80 ? 'text-emerald-600' : passRate >= 60 ? 'text-amber-500' : 'text-red-500'}`}>
                          {passRate}%
                        </span>
                      ) : (
                        <span className="text-[#c0c4cc]">-</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-[#86909c]">{task.createdAt}</td>
                    <td className="py-4 px-5 text-right">
                      <button
                        onClick={() => setSelectedTask(task)}
                        className="px-3 py-1.5 rounded-md text-[12px] text-[#0077ff] hover:bg-[#e8f3ff] transition-colors font-medium"
                      >
                        查看报告
                      </button>
                    </td>
                  </tr>
                );
              })}
              {tasks.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-14 text-center text-[#86909c]">
                    暂无评测任务
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="panel py-16 text-center">
          <ClipboardCheck size={36} className="mx-auto mb-3 text-[#d4d7de]" />
          <p className="text-[14px] text-[#86909c]">评测集管理功能</p>
          <p className="text-[12px] text-[#c0c4cc] mt-1">在这里维护标准化的评测用例集（规划中）</p>
        </div>
      )}

      {/* 评测报告弹窗 */}
      {selectedTask && (
        <div className="fixed inset-0 bg-[#0b1e3c]/40 backdrop-blur-[2px] flex items-center justify-center z-50" onClick={() => setSelectedTask(null)}>
          <div className="bg-white rounded-panel-lg w-[720px] max-h-[80vh] overflow-y-auto shadow-pop" onClick={(e) => e.stopPropagation()}>
            {/* 报告头部 */}
            <div className="px-6 py-5 border-b border-[#f2f3f5] flex items-center justify-between sticky top-0 bg-white">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#38b6ff] to-[#0077ff] text-white flex items-center justify-center">
                  <BarChart3 size={18} />
                </div>
                <div>
                  <h3 className="text-[15px] font-semibold text-[#1d2129]">评测报告 · {selectedTask.name}</h3>
                  <p className="text-[12px] text-[#86909c] mt-0.5">
                    {selectedTask.agentName} · {selectedTask.createdAt}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-[#f2f3f5] text-[#86909c]"
              >
                ✕
              </button>
            </div>

            {/* 概要指标 */}
            <div className="px-6 py-4 grid grid-cols-3 gap-4 border-b border-[#f2f3f5] bg-[#fafbfc]">
              <div className="text-center">
                <div className="text-[22px] font-semibold text-[#1d2129]">{caseList.length}</div>
                <div className="text-[11px] text-[#86909c] mt-1">评测用例</div>
              </div>
              <div className="text-center">
                <div className="text-[22px] font-semibold text-emerald-600">{caseList.filter((c) => c.status === 'passed').length}</div>
                <div className="text-[11px] text-[#86909c] mt-1">通过</div>
              </div>
              <div className="text-center">
                <div className="text-[22px] font-semibold text-red-500">{caseList.filter((c) => c.status === 'failed').length}</div>
                <div className="text-[11px] text-[#86909c] mt-1">未通过</div>
              </div>
            </div>

            {/* 用例明细 */}
            <div className="p-6">
              {caseList.map((c) => (
                <div key={c.id} className="mb-5 last:mb-0">
                  <div className="flex items-center gap-2.5 mb-2.5">
                    <span
                      className={`inline-flex w-5 h-5 items-center justify-center rounded-full text-white text-[10px] ${
                        c.status === 'passed' ? 'bg-emerald-500' : 'bg-red-500'
                      }`}
                    >
                      {c.status === 'passed' ? '✓' : '✕'}
                    </span>
                    <span className="text-[13px] text-[#1d2129] font-medium">{c.question}</span>
                    <span className="ml-auto text-[12px] text-[#86909c]">{Math.round(c.score * 100)}分</span>
                  </div>
                  <div className="ml-[26px] bg-[#fafbfc] border border-[#f0f1f3] rounded-md p-3 space-y-1.5 text-[12px]">
                    <div className="text-[#4e5969]">
                      <span className="text-[#86909c] mr-1">预期：</span>
                      {c.expected}
                    </div>
                    <div className={c.status === 'passed' ? 'text-emerald-600' : 'text-red-500'}>
                      <span className="text-[#86909c] mr-1">实际：</span>
                      {c.actual}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}