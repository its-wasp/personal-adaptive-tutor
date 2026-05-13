import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

/**
 * Shared markdown renderer used by chat bubbles.
 *
 * We lock down the component map so the LLM can't inject styling we
 * don't want (raw HTML is disabled by default in react-markdown).
 * The only customization is adding Tailwind `prose`-style classes via
 * components rather than pulling in @tailwindcss/typography — keeps
 * the bundle small and the look consistent with the rest of the UI.
 */
export default function MarkdownRenderer({ children, className = "" }) {
  return (
    <div className={"markdown text-sm leading-relaxed text-slate-800 " + className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          p: ({ node, ...props }) => <p className="mb-3 last:mb-0" {...props} />,
          h1: ({ node, ...props }) => (
            <h1 className="mb-2 mt-4 text-lg font-semibold text-slate-900" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="mb-2 mt-4 text-base font-semibold text-slate-900" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="mb-2 mt-3 text-sm font-semibold text-slate-900" {...props} />
          ),
          ul: ({ node, ...props }) => <ul className="mb-3 list-disc space-y-1 pl-5" {...props} />,
          ol: ({ node, ...props }) => <ol className="mb-3 list-decimal space-y-1 pl-5" {...props} />,
          code: ({ inline, className, children, ...props }) => {
            if (inline) {
              return (
                <code
                  className="rounded bg-slate-100 px-1 py-0.5 text-[0.85em] font-mono text-slate-900"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ node, ...props }) => (
            <pre
              className="mb-3 overflow-x-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100"
              {...props}
            />
          ),
          a: ({ node, ...props }) => (
            <a
              className="text-indigo-600 underline hover:text-indigo-700"
              target="_blank"
              rel="noreferrer"
              {...props}
            />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="mb-3 border-l-4 border-slate-300 pl-3 italic text-slate-600"
              {...props}
            />
          ),
          table: ({ node, ...props }) => (
            <div className="mb-3 overflow-x-auto">
              <table className="min-w-full border-collapse text-left text-xs" {...props} />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th className="border border-slate-300 bg-slate-100 px-2 py-1 font-semibold" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-slate-300 px-2 py-1" {...props} />
          ),
        }}
      >
        {children || ""}
      </ReactMarkdown>
    </div>
  );
}
