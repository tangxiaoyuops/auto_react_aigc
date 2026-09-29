// 完整的 Markdown 富文本渲染（基于 react-markdown + GFM + KaTeX + 代码高亮）
// 支持：标题 / 加粗 / 斜体 / 列表 / 引用 / 链接 / 表格 / 删除线 /
//       行内代码 / 代码块（语法高亮）/ 数学公式（$..$ 行内、$$..$$ 块公式）
import React from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeHighlight from 'rehype-highlight';

import 'katex/dist/katex.min.css';
import 'highlight.js/styles/github.css';

interface Props {
  content: string;
  className?: string;
}

const components: Components = {
  a: ({ href, children }) => {
    const target = href?.startsWith('http') ? '_blank' : undefined;
    const rel = target ? 'noopener noreferrer' : undefined;
    return (
      <a href={href} target={target} rel={rel} className="text-[#0077ff] hover:underline break-all">
        {children}
      </a>
    );
  },
};

// 最外层提供统一字体/字号，公式与正文风格一致
const PROSE_CLASS =
  'w-full text-[13px] leading-relaxed text-[#4e5969] ' +
  '[&>p]:my-1.5 ' +
  '[&>ul]:my-1.5 [&>ul]:pl-5 [&>ul]:list-disc ' +
  '[&>ol]:my-1.5 [&>ol]:pl-5 [&>ol]:list-decimal ' +
  '[&_li]:my-0.5 ' +
  '[&>h1]:text-[15px] [&>h1]:font-semibold [&>h1]:text-[#1d2129] [&>h1]:mt-2 [&>h1]:mb-1 ' +
  '[&>h2]:text-[14px] [&>h2]:font-semibold [&>h2]:text-[#1d2129] [&>h2]:mt-2 [&>h2]:mb-1 ' +
  '[&>h3]:text-[13px] [&>h3]:font-medium [&>h3]:text-[#1d2129] [&>h3]:mt-2 [&>h3]:mb-1 ' +
  '[&>h4]:text-[13px] [&>h4]:font-medium [&>h4]:text-[#1d2129] ' +
  '[&>blockquote]:my-1.5 [&>blockquote]:pl-3 [&>blockquote]:border-l-[3px] ' +
  '[&>blockquote]:border-[#38b6ff] [&>blockquote]:text-[#4e5969] [&>blockquote]:italic ' +
  '[&>hr]:my-2 [&>hr]:border-t [&>hr]:border-[#e5e6eb] ' +
  '[&_table]:my-2 [&_table]:text-[12px] [&_table]:w-full [&_table]:border-collapse ' +
  '[&_th]:px-2 [&_th]:py-1 [&_th]:bg-[#f5f7fa] [&_th]:font-medium ' +
  '[&_th]:border [&_th]:border-[#e5e6eb] [&_td]:px-2 [&_td]:py-1 ' +
  '[&_td]:border [&_td]:border-[#e5e6eb] ' +
  '[&_p>code]:px-1 [&_p>code]:py-0.5 [&_p>code]:rounded [&_p>code]:bg-[#f2f3f5] ' +
  '[&_p>code]:text-[#0077ff] [&_p>code]:font-mono [&_p>code]:text-[12px]';

export default function Markdown({ content, className = '' }: Props) {
  if (!content) return null;
  return (
    <ErrorBoundary fallback={<pre className="whitespace-pre-wrap text-[13px] text-[#4e5969]">{content}</pre>}>
      <div className={`${PROSE_CLASS} ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex, rehypeHighlight]}
          components={components}
        >
          {content}
        </ReactMarkdown>
      </div>
    </ErrorBoundary>
  );
}

// 简单错误边界：渲染异常（如流式中间态残缺的公式）时回退为纯文本，避免气泡空白
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidUpdate(prevProps: { children: React.ReactNode }) {
    if (prevProps.children !== this.props.children && this.state.hasError) {
      this.setState({ hasError: false }); // 内容更新后重新尝试渲染
    }
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}