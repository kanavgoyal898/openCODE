"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { CloneMatch, Repository, Scan } from "../lib/types";
import { CompareWorkspace } from "./CompareWorkspace";
import { SourceViewer } from "./SourceViewer";

export function Dashboard() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selected, setSelected] = useState("");
  const [scan, setScan] = useState<Scan | null>(null);
  const [clones, setClones] = useState<CloneMatch[]>([]);
  const [active, setActive] = useState<CloneMatch | null>(null);
  const [type, setType] = useState("");
  const [language, setLanguage] = useState("");
  const [error, setError] = useState("");
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    api.repositories().then(({ items }) => {
      setRepositories(items);
      setSelected(items[0]?.id ?? "");
    }).catch(cause => setError(String(cause)));
  }, []);

  async function addRepository(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const created = await api.createRepository(String(data.get("name")), String(data.get("path")));
      setRepositories(items => [...items, created]);
      setSelected(created.id);
      event.currentTarget.reset();
    } catch (cause) { setError(String(cause)); }
  }

  async function runScan() {
    if (!selected) return;
    setError("");
    setScanning(true);
    try {
      const queued = await api.startScan(selected);
      setScan(queued);
      let current = queued;
      for (let attempt = 0; attempt < 60 && ["queued", "running"].includes(current.status); attempt++) {
        await new Promise(resolve => setTimeout(resolve, 250));
        current = await api.scan(queued.id);
        setScan(current);
      }
      const response = await api.clones(selected, type || undefined);
      setClones(response.items);
      setActive(null);
    } catch (cause) { setError(String(cause)); }
    finally { setScanning(false); }
  }

  async function selectClone(match: CloneMatch) {
    if (!match.id) return;
    try { setActive(await api.clone(match.id)); }
    catch (cause) { setError(String(cause)); }
  }

  const filtered = clones.filter(match => !language || match.left.fragment_id.endsWith(`.${language}`) || match.right.fragment_id.endsWith(`.${language}`));

  return <main>
    <header className="site-header">
      <a className="brand" href="#top" aria-label="openCODE home"><span aria-hidden="true">⌁</span> openCODE</a>
      <nav aria-label="Primary"><a href="#compare">Compare</a><a href="#repositories">Repositories</a></nav>
      <span className="privacy-chip">Local-first analysis</span>
    </header>

    <div id="top" className="page-shell">
      <section className="hero">
        <p className="eyebrow">Evidence-based clone analysis</p>
        <h1>See what code has in common.</h1>
        <p>Compare two snippets instantly or inspect an entire repository with deterministic, explainable evidence.</p>
      </section>

      {error && <div role="alert" className="status-card error">{error}</div>}
      <div id="compare"><CompareWorkspace /></div>

      <section id="repositories" aria-labelledby="repositories-title" className="workspace-section">
        <div className="section-heading">
          <div><p className="eyebrow">Repository workspace</p><h2 id="repositories-title">Scan a codebase</h2></div>
          <p>Register an allowlisted local repository, run the detectors, then inspect verified source evidence.</p>
        </div>

        <div className="repository-layout">
          <aside className="control-stack">
            <details className="panel" open={repositories.length === 0}><summary>Add repository</summary><form onSubmit={addRepository} className="form-stack"><label>Name<input name="name" required placeholder="Payments service" /></label><label>Allowlisted local path<input name="path" required placeholder="/workspace/project" /></label><button className="secondary-button">Register repository</button></form></details>
            <section className="panel control-card"><h3>Scan controls</h3><label>Repository<select aria-label="Repository" value={selected} onChange={event => setSelected(event.target.value)}><option value="">Select a repository</option>{repositories.map(repository => <option value={repository.id} key={repository.id}>{repository.name}</option>)}</select></label><button onClick={runScan} disabled={!selected || scanning} className="primary-button">{scanning ? "Scanning…" : "Start scan"}</button>{scan && <div className="scan-status" aria-live="polite"><span className={`status-dot ${scan.status}`} />Status: <strong>{scan.status}</strong><dl>{Object.entries(scan.counts).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></div>}</section>
          </aside>

          <div className="results-stack">
            <section className="panel results-panel"><div className="results-header"><div><p className="eyebrow">Detection results</p><h3>{filtered.length} clone{filtered.length === 1 ? "" : "s"}</h3></div><div className="filter-row"><label>Type<select aria-label="Clone type" value={type} onChange={event => setType(event.target.value)}><option value="">All</option><option value="type1">Type 1</option><option value="type2">Type 2</option><option value="type3">Type 3</option><option value="type4">Type 4</option></select></label><label>Language<select aria-label="Language" value={language} onChange={event => setLanguage(event.target.value)}><option value="">All</option><option value="py">Python</option><option value="js">JavaScript</option><option value="ts">TypeScript</option><option value="java">Java</option></select></label></div></div>
              <div className="table-wrap"><table><thead><tr><th>Type</th><th>Evidence</th><th>Locations</th><th>Similarity</th></tr></thead><tbody>{filtered.map(match => <tr key={match.id}><td><button onClick={() => selectClone(match)} className="text-button">{match.category}</button></td><td><span className="evidence-chip">{match.evidence_state}</span></td><td><span className="path-pair">{match.left.fragment_id}<i>↔</i>{match.right.fragment_id}</span></td><td>{Math.round(match.scores.token_jaccard * 100)}%</td></tr>)}</tbody></table>{filtered.length === 0 && <div className="empty-state"><span aria-hidden="true">⌁</span><p>No clone results for the active filters.</p><small>Start a scan or adjust your filters.</small></div>}</div>
            </section>

            {active && <section aria-label="Selected clone evidence" className="evidence-section"><dl className="metric-grid panel"><div><dt>Detector</dt><dd>{active.detector_id}</dd></div><div><dt>Algorithm</dt><dd>{active.algorithm_version}</dd></div><div><dt>Fingerprint Jaccard</dt><dd>{active.scores.fingerprint_jaccard?.toFixed(3) ?? "n/a"}</dd></div><div><dt>Token Jaccard</dt><dd>{active.scores.token_jaccard.toFixed(3)}</dd></div><div className="wide-metric"><dt>Why matched</dt><dd>{active.evidence.explanation_codes.join(", ")}</dd><small>{active.limitations.join(" · ")}</small></div></dl><div className="source-grid"><SourceViewer title="Left fragment" source={active.leftSource} range={active.left} /><SourceViewer title="Right fragment" source={active.rightSource} range={active.right} /></div></section>}
          </div>
        </div>
      </section>

      <footer><p>Similarity explains shared code structure. It is not proof of plagiarism, authorship, or semantic equivalence.</p></footer>
    </div>
  </main>;
}
