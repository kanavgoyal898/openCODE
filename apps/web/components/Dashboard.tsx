"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { CloneMatch, Repository, Scan } from "../lib/types";
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

  useEffect(() => { api.repositories().then(({ items }) => { setRepositories(items); setSelected(items[0]?.id ?? ""); }).catch(e => setError(String(e))); }, []);

  async function addRepository(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    try { const created = await api.createRepository(String(data.get("name")), String(data.get("path"))); setRepositories(items => [...items, created]); setSelected(created.id); event.currentTarget.reset(); }
    catch (cause) { setError(String(cause)); }
  }

  async function runScan() {
    if (!selected) return;
    try {
      const queued = await api.startScan(selected); setScan(queued);
      let current = queued;
      for (let attempt = 0; attempt < 60 && ["queued", "running"].includes(current.status); attempt++) {
        await new Promise(resolve => setTimeout(resolve, 250)); current = await api.scan(queued.id); setScan(current);
      }
      const response = await api.clones(selected, type || undefined); setClones(response.items); setActive(null);
    } catch (cause) { setError(String(cause)); }
  }

  async function selectClone(match: CloneMatch) { try { setActive(await api.clone(match.id)); } catch (cause) { setError(String(cause)); } }
  const filtered = clones.filter(match => !language || match.left.fragment_id.endsWith(`.${language}`) || match.right.fragment_id.endsWith(`.${language}`));

  return <main className="mx-auto max-w-[1500px] p-5 md:p-8">
    <header className="mb-8"><p className="text-sm text-[var(--accent)]">openCODE / evidence console</p><h1 className="text-3xl font-semibold">Clone analysis workspace</h1><p className="muted mt-2 max-w-3xl">Similarity explains shared code structure. It is not proof of plagiarism, authorship, or semantic equivalence.</p></header>
    {error && <div role="alert" className="mb-5 rounded border border-red-400 bg-red-950 p-3">{error}</div>}
    <div className="grid gap-5 lg:grid-cols-[340px_1fr]">
      <aside className="space-y-5">
        <section className="panel p-4"><h2 className="mb-3 font-semibold">Add repository</h2><form onSubmit={addRepository} className="space-y-3"><label className="block text-sm">Name<input name="name" required className="mt-1 w-full rounded bg-black/30 p-2" /></label><label className="block text-sm">Allowlisted local path<input name="path" required className="mt-1 w-full rounded bg-black/30 p-2" /></label><button className="rounded bg-teal-300 px-3 py-2 font-semibold text-slate-950">Register</button></form></section>
        <section className="panel p-4"><h2 className="mb-3 font-semibold">Scan controls</h2><label className="block text-sm">Repository<select aria-label="Repository" value={selected} onChange={e => setSelected(e.target.value)} className="mt-1 w-full rounded bg-black/30 p-2">{repositories.map(repository => <option value={repository.id} key={repository.id}>{repository.name}</option>)}</select></label><button onClick={runScan} disabled={!selected} className="mt-3 rounded border border-[var(--accent)] px-3 py-2 disabled:opacity-40">Start scan</button>{scan && <div className="mt-4" aria-live="polite"><p>Status: <strong>{scan.status}</strong></p><dl className="mt-2 grid grid-cols-2 gap-2 text-sm">{Object.entries(scan.counts).map(([key, value]) => <div key={key}><dt className="muted">{key}</dt><dd>{value}</dd></div>)}</dl></div>}</section>
      </aside>
      <section className="space-y-5">
        <div className="panel p-4"><div className="flex flex-wrap items-end gap-3"><h2 className="mr-auto text-xl font-semibold">Clone results</h2><label className="text-sm">Clone type<select aria-label="Clone type" value={type} onChange={e => setType(e.target.value)} className="ml-2 rounded bg-black/30 p-2"><option value="">All</option><option value="type1">Type 1</option><option value="type2">Type 2</option><option value="type3">Type 3</option><option value="type4">Type 4</option></select></label><label className="text-sm">Language<select aria-label="Language" value={language} onChange={e => setLanguage(e.target.value)} className="ml-2 rounded bg-black/30 p-2"><option value="">All</option><option value="py">Python</option><option value="js">JavaScript</option><option value="ts">TypeScript</option><option value="java">Java</option></select></label></div><div className="mt-4 overflow-auto"><table className="w-full text-left text-sm"><thead className="muted"><tr><th className="p-2">Type</th><th>Evidence</th><th>Locations</th><th>Token score</th></tr></thead><tbody>{filtered.map(match => <tr key={match.id} className="border-t border-[var(--line)]"><td className="p-2"><button onClick={() => selectClone(match)} className="text-[var(--accent)] underline">{match.category}</button></td><td>{match.evidence_state}</td><td>{match.left.fragment_id} ↔ {match.right.fragment_id}</td><td>{match.scores.token_jaccard.toFixed(3)}</td></tr>)}</tbody></table>{filtered.length === 0 && <p className="muted py-6 text-center">No clone results for the active filters.</p>}</div></div>
        {active && <section aria-label="Selected clone evidence" className="space-y-4"><div className="panel grid gap-3 p-4 md:grid-cols-4"><div><span className="muted text-xs">Detector</span><p>{active.detector_id}</p></div><div><span className="muted text-xs">Algorithm</span><p>{active.algorithm_version}</p></div><div><span className="muted text-xs">Fingerprint Jaccard</span><p>{active.scores.fingerprint_jaccard?.toFixed(3) ?? "n/a"}</p></div><div><span className="muted text-xs">Token Jaccard</span><p>{active.scores.token_jaccard.toFixed(3)}</p></div><div className="md:col-span-4"><span className="muted text-xs">Why matched</span><p>{active.evidence.explanation_codes.join(", ")}</p><p className="mt-1 text-xs text-[var(--warning)]">{active.limitations.join(" · ")}</p></div></div><div className="grid gap-4 xl:grid-cols-2"><SourceViewer title="Left fragment" source={active.leftSource} range={active.left} /><SourceViewer title="Right fragment" source={active.rightSource} range={active.right} /></div></section>}
      </section>
    </div>
  </main>;
}
