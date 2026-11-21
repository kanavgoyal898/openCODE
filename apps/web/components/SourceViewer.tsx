import type { SourceRange } from "../lib/types";

export function SourceViewer({ title, source, range }: { title: string; source?: string; range: SourceRange }) {
  const lines = (source ?? "Source text is unavailable under the active retention policy.").split("\n");
  return (
    <section className="panel min-w-0 overflow-hidden" aria-label={title}>
      <h3 className="border-b border-[var(--line)] px-4 py-3 text-sm">{title}: {range.fragment_id}</h3>
      <pre className="max-h-96 overflow-auto p-3 text-xs leading-6" tabIndex={0}>
        {lines.map((line, index) => {
          const number = index + 1;
          const matched = number >= range.start_line && number <= range.end_line;
          return <div key={number} className={matched ? "matched" : ""}><span className="muted inline-block w-10 text-right pr-3">{number}</span>{line || " "}</div>;
        })}
      </pre>
    </section>
  );
}
