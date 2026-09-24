// 轻量 Markdown 渲染（纯 TS，零依赖）
// 覆盖 LLM 回复常见格式：标题 / 段落 / 加粗 / 斜体 / 有序列表 / 无序列表 / 引用 / 行内代码 / 代码块 / 分割线
import React from 'react';

interface Props {
  content: string;
  className?: string;
}

// 行内样式：**加粗**、*斜体*、`行内代码`
// 流式兼容：未闭合的 ** / * / ` （SSE 分段中间态）不显示裸符号，避免闪烁
function renderInline(text: string, keyBase: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`\n]+`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > last) parts.push(sanitizeOpenToken(text.slice(last, m.index)));
    const token = m[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      parts.push(
        <strong key={`${keyBase}-${i}`} className="font-semibold text-[#1d2129]">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      parts.push(
        <code
          key={`${keyBase}-${i}`}
          className="px-1 py-0.5 rounded bg-[#f2f3f5] text-[#0077ff] font-mono text-[12px]"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else {
      parts.push(
        <em key={`${keyBase}-${i}`} className="italic text-[#4e5969]">
          {token.slice(1, -1)}
        </em>
      );
    }
    i += 1;
    last = m.index + token.length;
  }
  if (last < text.length) parts.push(sanitizeOpenToken(text.slice(last)));
  return parts;
}

// 清除流式中间态遗留的孤立 markdown 标记（未闭合的 ** / * / `）
function sanitizeOpenToken(text: string): string {
  if (!text) return text;
  return text.replace(/\*\*|\*|`/g, '');
}

// 把一行拆成「前缀列表项 + 行内内容」
function renderLine(line: string, key: string): React.ReactNode {
  return <>{renderInline(line, key)}</>;
}

function renderBlock(lines: string[], idx: number): React.ReactNode {
  const line = lines[idx];
  const trimmed = line.trim();

  // 分割线 ---
  if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
    return <hr key={idx} className="my-2 border-t border-[#e5e6eb]" />;
  }

  // 代码块（``` ... ```）
  if (trimmed.startsWith('```')) {
    const codeLines: string[] = [];
    let j = idx + 1;
    while (j < lines.length && !lines[j].trim().startsWith('```')) {
      codeLines.push(lines[j]);
      j += 1;
    }
    return (
      <pre
        key={idx}
        className="my-1.5 px-3 py-2.5 rounded-md bg-[#1d2129] text-[#d4d7de] font-mono text-[12px] leading-relaxed overflow-x-auto whitespace-pre"
      >
        {codeLines.join('\n')}
      </pre>
    );
  }

  // 标题
  const h = /^(#{1,4})\s+(.*)$/.exec(trimmed);
  if (h) {
    const level = h[1].length;
    const cls =
      level === 1
        ? 'text-[15px] font-semibold'
        : level === 2
        ? 'text-[14px] font-semibold'
        : 'text-[13px] font-medium';
    return (
      <div key={idx} className={`${cls} text-[#1d2129] mt-2 mb-1`}>
        {renderInline(h[2], `h-${idx}`)}
      </div>
    );
  }

  // 引用
  if (trimmed.startsWith('>')) {
    return (
      <blockquote
        key={idx}
        className="my-1.5 pl-3 border-l-[3px] border-[#38b6ff] text-[#4e5969] italic"
      >
        {renderLine(trimmed.replace(/^>\s?/, ''), `q-${idx}`)}
      </blockquote>
    );
  }

  // 无序列表 - / * / •
  const ul = /^[-*•]\s+(.*)$/.exec(trimmed);
  if (ul) {
    return (
      <div key={idx} className="flex gap-2 my-0.5">
        <span className="text-[#0077ff] shrink-0 mt-[2px]">•</span>
        <span className="flex-1 min-w-0">{renderLine(ul[1], `ul-${idx}`)}</span>
      </div>
    );
  }

  // 有序列表 1. / 1）
  const ol = /^(\d+)[.、)]\s+(.*)$/.exec(trimmed);
  if (ol) {
    return (
      <div key={idx} className="flex gap-2 my-0.5">
        <span className="text-[#86909c] shrink-0 w-5 text-right font-mono">{ol[1]}.</span>
        <span className="flex-1 min-w-0">{renderLine(ol[2], `ol-${idx}`)}</span>
      </div>
    );
  }

  // 普通段落（合并连续非空行成一段）
  const para: string[] = [line];
  let j = idx + 1;
  while (j < lines.length && lines[j].trim() !== '') {
    para.push(lines[j]);
    j += 1;
  }
  return (
    <p key={idx} className="my-1.5 leading-relaxed text-[13px] text-[#4e5969]">
      {renderLine(para.join('\n'), `p-${idx}`)}
    </p>
  );
}

export default function Markdown({ content, className = '' }: Props) {
  if (!content) return null;
  const lines = content.split('\n');
  const nodes: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const trimmed = lines[i].trim();
    if (trimmed === '') {
      i += 1;
      continue;
    }
    // 代码块整体跳过
    if (trimmed.startsWith('```')) {
      const codeLines: string[] = [];
      let j = i + 1;
      while (j < lines.length && !lines[j].trim().startsWith('```')) {
        codeLines.push(lines[j]);
        j += 1;
      }
      nodes.push(
        <pre
          key={`cb-${i}`}
          className="my-1.5 px-3 py-2.5 rounded-md bg-[#1d2129] text-[#d4d7de] font-mono text-[12px] leading-relaxed overflow-x-auto whitespace-pre"
        >
          {codeLines.join('\n')}
        </pre>
      );
      i = j + 1;
      continue;
    }
    const node = renderBlock(lines, i);
    nodes.push(node);
    // renderBlock 已消费掉段落/代码块，计算跳过行数
    const consumed = countConsumed(lines, i);
    i = consumed;
  }
  return <div className={`text-left ${className}`}>{nodes}</div>;
}

function countConsumed(lines: string[], idx: number): number {
  const trimmed = lines[idx].trim();
  if (trimmed.startsWith('```')) {
    let j = idx + 1;
    while (j < lines.length && !lines[j].trim().startsWith('```')) j += 1;
    return j + 1;
  }
  if (/^(#{1,4})\s+/.test(trimmed)) return idx + 1;
  if (/^(-{3,}|\*{3,})$/.test(trimmed)) return idx + 1;
  if (/^>\s?/.test(trimmed)) return idx + 1;
  if (/^[-*•]\s+/.test(trimmed)) return idx + 1;
  if (/^\d+[.、)]\s+/.test(trimmed)) return idx + 1;
  // 普通段落：吞掉后续连续非空行
  let j = idx + 1;
  while (j < lines.length && lines[j].trim() !== '') j += 1;
  return j;
}
