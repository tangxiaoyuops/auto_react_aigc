import { defineTool } from '@deepseek-ai/dsh-tools'
import type { Context } from '@deepseek-ai/cordis'

/** 安全地执行数学表达式（harness 版 Calculator，对接前端 tool_calculator）。 */
function safeEval(expression: string): number | null {
  // 仅允许数字、四则运算、括号、小数点、一元正负号
  if (!/^[0-9+\-*/().\s]+$/.test(expression)) return null
  try {
    // eslint-disable-next-line no-new-func
    const fn = new Function(`"use strict"; return (${expression});`)
    const value = fn()
    return typeof value === 'number' && Number.isFinite(value) ? value : null
  } catch {
    return null
  }
}

export const name = 'calculator-tool'
export const inject = ['tools']

export function apply(ctx: Context) {
  ctx.tools.register(defineTool({
    name: 'calculator',
    description: '安全地执行一个数学表达式计算，例如 (12+34)*2。用于需要精确数值计算的场景。',
    parameters: {
      expression: { type: 'string', required: true, description: '要计算的数学表达式' },
    },
    output: {
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          success: { type: 'boolean' },
          expression: { type: 'string' },
          result: { type: 'number' },
          error: { type: 'string' },
        },
      },
      render: (_args, value) => [
        { type: 'text', text: value.success
          ? `${value.expression} = ${value.result}`
          : `计算失败：${value.error ?? '不支持的表达式'}` },
      ],
    },
    async execute(args) {
      const result = safeEval(args.expression)
      if (result === null) {
        return { success: false, expression: args.expression, result: 0, error: '不支持的表达式' }
      }
      return { success: true, expression: args.expression, result }
    },
  }))

  console.log('[calculator-tool] loaded')
}