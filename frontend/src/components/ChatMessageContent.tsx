/** Lightweight markdown-style renderer for chat bubbles (no extra deps). */

import type { ReactNode } from 'react'

function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return <span key={i}>{part}</span>
  })
}

function isTableRow(line: string) {
  return line.includes('|') && line.trim().startsWith('|')
}

function isTableSeparator(line: string) {
  return /^\|?[\s\-:|]+\|?$/.test(line.trim())
}

function parseTable(rows: string[]) {
  const cells = rows
    .filter(r => !isTableSeparator(r))
    .map(r => r.split('|').map(c => c.trim()).filter(Boolean))
  if (!cells.length) return null
  const [header, ...body] = cells
  return { header, body }
}

export function ChatMessageContent({ content, isUser }: { content: string; isUser?: boolean }) {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  let listItems: string[] = []
  let listOrdered = false
  let tableRows: string[] = []

  const flushList = () => {
    if (!listItems.length) return
    const Tag = listOrdered ? 'ol' : 'ul'
    blocks.push(
      <Tag key={`list-${blocks.length}`} className={`my-2 space-y-1 ${listOrdered ? 'list-decimal' : 'list-disc'} ml-5`}>
        {listItems.map((item, idx) => (
          <li key={idx}>{renderInline(item)}</li>
        ))}
      </Tag>,
    )
    listItems = []
    listOrdered = false
  }

  const flushTable = () => {
    if (!tableRows.length) return
    const table = parseTable(tableRows)
    tableRows = []
    if (!table) return
    blocks.push(
      <div key={`table-${blocks.length}`} className="my-3 overflow-x-auto rounded-lg border border-slate-200/80 dark:border-slate-600/80">
        <table className="w-full text-xs sm:text-sm">
          <thead>
            <tr className={isUser ? 'bg-white/10' : 'bg-slate-200/60 dark:bg-slate-700/60'}>
              {table.header.map((h, idx) => (
                <th key={idx} className="px-3 py-2 text-left font-semibold">{renderInline(h)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.body.map((row, ridx) => (
              <tr key={ridx} className={isUser ? 'border-t border-white/20' : 'border-t border-slate-200 dark:border-slate-600'}>
                {row.map((cell, cidx) => (
                  <td key={cidx} className="px-3 py-2 align-top">{renderInline(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>,
    )
  }

  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()

    if (isTableRow(trimmed)) {
      flushList()
      tableRows.push(trimmed)
      i++
      continue
    }
    if (tableRows.length) flushTable()

    const bullet = trimmed.match(/^[-*•]\s+(.+)/)
    const numbered = trimmed.match(/^\d+[.)]\s+(.+)/)

    if (bullet) {
      if (listOrdered && listItems.length) flushList()
      listOrdered = false
      listItems.push(bullet[1])
      i++
      continue
    }
    if (numbered) {
      if (!listOrdered && listItems.length) flushList()
      listOrdered = true
      listItems.push(numbered[1])
      i++
      continue
    }

    if (listItems.length) flushList()

    if (!trimmed) {
      i++
      continue
    }

    blocks.push(
      <p key={`p-${blocks.length}`} className="my-1.5 leading-relaxed">
        {renderInline(trimmed)}
      </p>,
    )
    i++
  }

  flushList()
  flushTable()

  return <div className="space-y-0.5">{blocks}</div>
}
