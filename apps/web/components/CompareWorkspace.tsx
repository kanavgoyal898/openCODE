"use client";

import { FormEvent, useState } from "react";
import { api } from "../lib/api";
import type { CloneMatch, CompareMode, Language } from "../lib/types";

const EXAMPLES = {
  left: "def calculate_total(items, tax_rate):\n    subtotal = 0\n    for item in items:\n        subtotal += item.price * item.quantity\n    tax = subtotal * tax_rate\n    total = subtotal + tax\n    return round(total, 2)",
  right: "def sum_prices(products, rate):\n    amount = 0\n    for product in products:\n        amount += product.price * product.quantity\n    fee = amount * rate\n    result = amount + fee\n    return round(result, 2)",
};

export function CompareWorkspace() {
  const [leftCode, setLeftCode] = useState(EXAMPLES.left);
  const [rightCode, setRightCode] = useState(EXAMPLES.right);
  const [language, setLanguage] = useState<Language>("python");
  const [mode, setMode] = useState<CompareMode>("renamed");
  const [results, setResults] = useState<CloneMatch[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function compare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    setResults(null);
    try {
      const response = await api.compare(leftCode, rightCode, language, mode);
      setResults(response.items);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setLoading(false);
    }
  }

  const best = results?.[0];
  return (
    <section aria-labelledby="compare-title" className="workspace-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Direct comparison</p>
          <h2 id="compare-title">Compare two snippets</h2>
        </div>
        <p>Paste two fragments to check exact or rename-normalized overlap. Your snippets are processed ephemerally.</p>
      </div>

      <form onSubmit={compare}>
        <div className="compare-grid">
          <label className="code-field">
            <span><b>Snippet A</b><small>{leftCode.length.toLocaleString()} characters</small></span>
            <textarea aria-label="Snippet A" value={leftCode} onChange={event => setLeftCode(event.target.value)} required spellCheck={false} />
          </label>
          <label className="code-field">
            <span><b>Snippet B</b><small>{rightCode.length.toLocaleString()} characters</small></span>
            <textarea aria-label="Snippet B" value={rightCode} onChange={event => setRightCode(event.target.value)} required spellCheck={false} />
          </label>
        </div>
        <div className="compare-actions">
          <label>Language<select aria-label="Comparison language" value={language} onChange={event => setLanguage(event.target.value as Language)}><option value="python">Python</option><option value="javascript">JavaScript</option><option value="typescript">TypeScript</option><option value="java">Java</option></select></label>
          <label>Mode<select aria-label="Comparison mode" value={mode} onChange={event => setMode(event.target.value as CompareMode)}><option value="exact">Exact tokens</option><option value="renamed">Allow renames</option></select></label>
          <button className="primary-button" type="submit" disabled={loading}>{loading ? "Comparing…" : "Compare snippets"}</button>
        </div>
      </form>

      <div aria-live="polite" aria-atomic="true">
        {error && <p className="status-card error" role="alert">{error}</p>}
        {results && !best && <p className="status-card">No verified {mode} match was found.</p>}
        {best && <div className="result-card">
          <div className="result-summary"><span className="result-icon" aria-hidden="true">✓</span><div><p className="eyebrow">Verified match</p><h3>{best.category.toUpperCase()} similarity detected</h3><p>{best.evidence.explanation_codes.join(" · ")}</p></div><strong>{Math.round(best.scores.token_jaccard * 100)}%</strong></div>
          <dl className="metric-grid"><div><dt>Token similarity</dt><dd>{best.scores.token_jaccard.toFixed(3)}</dd></div><div><dt>Query coverage</dt><dd>{best.scores.query_coverage.toFixed(3)}</dd></div><div><dt>Candidate coverage</dt><dd>{best.scores.candidate_coverage.toFixed(3)}</dd></div><div><dt>Detector</dt><dd>{best.detector_id}</dd></div></dl>
          <p className="caveat">Similarity is evidence of shared structure—not proof of plagiarism, authorship, or semantic equivalence.</p>
        </div>}
      </div>
    </section>
  );
}
