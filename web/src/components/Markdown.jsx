import ReactMarkdown from 'react-markdown'
import remarkBreaks from 'remark-breaks'
import remarkGfm from 'remark-gfm'

// Compact styles for agent answers in small chat bubbles. Raw HTML in the text is not
// rendered (react-markdown's default), so model output can't inject markup.
const PLUGINS = [remarkGfm, remarkBreaks] // single newlines stay line breaks, as agents write them

const components = {
  p: ({ node: _n, ...props }) => <p className="my-1 first:mt-0 last:mb-0" {...props} />,
  h1: ({ node: _n, ...props }) => <h3 className="font-bold text-slate-900 text-[13px] mt-2 mb-1 first:mt-0" {...props} />,
  h2: ({ node: _n, ...props }) => <h3 className="font-bold text-slate-900 text-[12px] mt-2 mb-1 first:mt-0" {...props} />,
  h3: ({ node: _n, ...props }) => <h4 className="font-semibold text-slate-900 mt-2 mb-0.5 first:mt-0" {...props} />,
  h4: ({ node: _n, ...props }) => <h4 className="font-semibold text-slate-900 mt-2 mb-0.5 first:mt-0" {...props} />,
  ul: ({ node: _n, ...props }) => <ul className="list-disc pl-4 my-1 space-y-0.5" {...props} />,
  ol: ({ node: _n, ...props }) => <ol className="list-decimal pl-4 my-1 space-y-0.5" {...props} />,
  li: ({ node: _n, ...props }) => <li className="pl-0.5" {...props} />,
  strong: ({ node: _n, ...props }) => <strong className="font-semibold text-slate-900" {...props} />,
  a: ({ node: _n, href, ...props }) => <a href={href} target="_blank" rel="noreferrer noopener" className="text-[#2563EB] underline" {...props} />,
  code: ({ node: _n, ...props }) => <code className="font-mono text-[11px] bg-slate-200/70 rounded px-1" {...props} />,
  pre: ({ node: _n, ...props }) => <pre className="font-mono text-[11px] bg-slate-100 rounded p-2 my-1 overflow-x-auto [&_code]:bg-transparent [&_code]:p-0" {...props} />,
  blockquote: ({ node: _n, ...props }) => <blockquote className="border-l-2 border-slate-300 pl-2 my-1 text-slate-600" {...props} />,
  hr: () => <hr className="my-2 border-slate-200" />,
  table: (props) => (
    <div className="overflow-x-auto my-1.5">
      <table className="w-full border-collapse text-[11px]" {...props} />
    </div>
  ),
  th: ({ node: _n, ...props }) => <th className="border border-slate-200 bg-slate-100 px-1.5 py-1 text-left font-semibold" {...props} />,
  td: ({ node: _n, ...props }) => <td className="border border-slate-200 px-1.5 py-1 align-top" {...props} />,
}

/** Renders an agent's Markdown answer (GitHub-flavored: lists, tables, bold, code). */
export default function Markdown({ children, className = '' }) {
  return (
    <div className={`leading-relaxed break-words ${className}`}>
      <ReactMarkdown remarkPlugins={PLUGINS} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
