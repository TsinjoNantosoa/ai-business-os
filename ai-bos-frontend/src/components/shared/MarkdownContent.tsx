import { cn } from '@/lib/utils';

/** Lightweight markdown for Copilot replies (bold, italic, lists, code) — no extra deps. */
export function MarkdownContent({
  content,
  className,
  streaming,
}: {
  content: string
  className?: string
  streaming?: boolean
}) {
  const html = markdownToSafeHtml(content);
  return (
    <div className={cn('markdown-content leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:font-semibold [&_em]:italic [&_code]:rounded [&_code]:bg-black/5 [&_code]:px-1 [&_code]:text-[0.9em]', className)}>
      <span dangerouslySetInnerHTML={{ __html: html }} />
      {streaming && <span className="ml-0.5 inline-block h-3 w-1 animate-pulse bg-current align-middle" />}
    </div>
  );
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function inlineFormat(text: string): string {
  let out = escapeHtml(text);
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/_([^_]+)_/g, '<em>$1</em>');
  out = out.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, '$1<em>$2</em>');
  return out;
}

function markdownToSafeHtml(src: string): string {
  if (!src) return '';
  const lines = src.replace(/\r\n/g, '\n').split('\n');
  const parts: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(`<li>${inlineFormat(lines[i].replace(/^[-*]\s+/, ''))}</li>`);
        i += 1;
      }
      parts.push(`<ul>${items.join('')}</ul>`);
      continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(`<li>${inlineFormat(lines[i].replace(/^\d+\.\s+/, ''))}</li>`);
        i += 1;
      }
      parts.push(`<ol>${items.join('')}</ol>`);
      continue;
    }
    if (/^###\s+/.test(line)) {
      parts.push(`<p class="font-semibold text-[0.95em]">${inlineFormat(line.replace(/^###\s+/, ''))}</p>`);
      i += 1;
      continue;
    }
    if (/^##\s+/.test(line)) {
      parts.push(`<p class="font-semibold">${inlineFormat(line.replace(/^##\s+/, ''))}</p>`);
      i += 1;
      continue;
    }
    const para: string[] = [];
    while (i < lines.length && lines[i].trim() && !/^[-*]\s+/.test(lines[i]) && !/^\d+\.\s+/.test(lines[i])) {
      para.push(lines[i]);
      i += 1;
    }
    parts.push(`<p>${inlineFormat(para.join(' '))}</p>`);
  }
  return parts.join('');
}
