import { useCallback, useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import * as api from "./services/api";
import type { CardResult, Health, Job, Lead, LeadField, UploadConfig } from "./types/leads";
import { FilePreview } from "./components/FilePreview";
import { ResultsTable } from "./components/ResultsTable";

const defaults: UploadConfig = {
  max_files: 20, max_upload_mb: 10, job_ttl_seconds: 900,
  accepted_extensions: [".jpg", ".jpeg", ".png", ".webp"],
};
type SelectedFile = { id: string; file: File };
const terminal = (job: Job | null) => job?.status === "completed" || job?.status === "failed";

export default function App() {
  const [settings, setSettings] = useState(defaults);
  const [health, setHealth] = useState<Health | null>(null);
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<CardResult[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [pollPaused, setPollPaused] = useState(false);
  const picker = useRef<HTMLInputElement>(null);
  const processing = !!jobId && !terminal(job);
  const busy = uploading || processing;

  useEffect(() => {
    let active = true;
    const update = async () => {
      try { const state = await api.health(); if (active) setHealth(state); }
      catch { if (active) setHealth(null); }
    };
    void update();
    void api.config().then(value => { if (active) setSettings(value); }).catch(() => {});
    const interval = window.setInterval(() => void update(), 10000);
    return () => { active = false; window.clearInterval(interval); };
  }, []);

  useEffect(() => {
    if (!jobId || terminal(job) || pollPaused) return;
    let active = true;
    let timer: number | undefined;
    let failures = 0;
    const poll = async () => {
      try {
        const value = await api.getJob(jobId);
        if (!active) return;
        failures = 0;
        setJob(value);
        setResults(value.leads);
        if (terminal(value)) {
          setNotice(value.successful
            ? "Extraction complete. Review every field before exporting."
            : "No leads extracted. Check the card errors below.");
          if (value.error) setError(value.error);
          return;
        }
      } catch (cause) {
        if (!active) return;
        failures += 1;
        if ((cause instanceof api.ApiError && cause.status === 404) || failures >= 3) {
          setPollPaused(true);
          setError(cause instanceof Error ? cause.message : "Could not retrieve results.");
          return;
        }
      }
      timer = window.setTimeout(() => void poll(), 1500);
    };
    void poll();
    return () => { active = false; if (timer) window.clearTimeout(timer); };
  }, [jobId, job?.status, pollPaused]);

  const addFiles = useCallback((incoming: File[]) => {
    if (busy || jobId) return;
    const accepted: SelectedFile[] = [];
    const problems: string[] = [];
    for (const file of incoming) {
      const suffix = "." + (file.name.split(".").pop() || "").toLowerCase();
      if (!settings.accepted_extensions.includes(suffix)) problems.push(file.name + ": use JPG, PNG, or WEBP.");
      else if (!file.size || file.size > settings.max_upload_mb * 1024 * 1024) problems.push(file.name + ": empty or exceeds " + settings.max_upload_mb + " MB.");
      else if (files.length + accepted.length >= settings.max_files) problems.push("A batch can contain at most " + settings.max_files + " cards.");
      else if (!files.some(item => item.file.name === file.name && item.file.size === file.size && item.file.lastModified === file.lastModified)
        && !accepted.some(item => item.file.name === file.name && item.file.size === file.size && item.file.lastModified === file.lastModified)) {
        accepted.push({ id: String(Date.now()) + "-" + String(Math.random()), file });
      }
    }
    setFiles(current => [...current, ...accepted]);
    setError([...new Set(problems)].slice(0, 3).join(" "));
    setNotice("");
  }, [busy, jobId, settings, files]);

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); setDragging(false); addFiles(Array.from(event.dataTransfer.files));
  }
  function onPick(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files || [])); event.target.value = "";
  }
  async function start() {
    if (!files.length || busy) return;
    setUploading(true); setError(""); setNotice(""); setResults([]); setPollPaused(false);
    try {
      const value = await api.extract(files.map(item => item.file));
      setJob(value); setJobId(value.job_id); setResults(value.leads);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Upload failed."); }
    finally { setUploading(false); }
  }
  async function clear() {
    if (busy && !pollPaused) return;
    if (jobId) {
      try { await api.deleteJob(jobId); }
      catch (cause) { setError(cause instanceof Error ? cause.message : "Could not clear results."); return; }
    }
    setJob(null); setJobId(null); setFiles([]); setResults([]); setError(""); setNotice(""); setPollPaused(false);
  }
  function edit(index: number, field: LeadField, value: string) {
    setResults(current => current.map(result => result.index === index && result.lead
      ? { ...result, lead: { ...result.lead, [field]: value || null } } : result));
  }
  async function download() {
    setExporting(true); setError("");
    try {
      const leads = results.filter(result => result.status === "success" && result.lead).map(result => result.lead as Lead);
      await api.exportLeads(leads); setNotice("Excel download started with your reviewed values.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Excel export failed."); }
    finally { setExporting(false); }
  }

  const successCount = results.filter(result => result.status === "success").length;
  const failed = results.filter(result => result.status === "error");
  const statusText = !health ? "Connecting to server" : health.model_loaded ? "Qwen is ready"
    : health.model_state === "loading" ? "Qwen is starting" : health.model_state === "disabled" ? "Inference is disabled" : "Model unavailable";

  return <div className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Business Card Lead Extractor home">
        <span className="brand-mark" aria-hidden="true">bc<span>•</span></span><span>Card to contact</span>
      </a>
      <div className={"server-status " + (health?.model_loaded ? "ready" : "")}><span />{statusText}</div>
    </header>
    <main>
      <section className="hero">
        <div className="eyebrow">LESS ADMIN. MORE CONNECTIONS.</div>
        <h1>Good conversations.<br /><em>Organized contacts.</em></h1>
        <p>Convert business cards into structured leads using Qwen Vision-Language AI. Upload, review, and take your next connection forward.</p>
        <div className="workflow" aria-label="Workflow"><span><b>01</b> Upload cards</span><i aria-hidden="true">→</i><span><b>02</b> Review leads</span><i aria-hidden="true">→</i><span><b>03</b> Export Excel</span></div>
      </section>

      {error && <div className="alert error" role="alert">{error}</div>}
      {notice && <div className="alert notice" role="status">{notice}</div>}
      {pollPaused && <div className="recovery">
        <button className="button secondary" onClick={() => { setError(""); setPollPaused(false); }}>Reconnect to batch</button>
        <button className="text-button" onClick={() => void clear()}>Clear finished or expired batch</button>
        <p>A connection error does not cancel processing on the server.</p>
      </div>}

      <section className="panel upload-panel" aria-labelledby="upload-heading">
        <div className="section-heading"><div><span className="step-label">01 / INPUT</span><h2 id="upload-heading">Your next batch of connections</h2></div>
          <span className="count-pill">{files.length} / {settings.max_files} cards</span></div>
        <div className={"dropzone " + (dragging ? "dragging " : "") + (busy || jobId ? "locked" : "")}
          onDragOver={event => { event.preventDefault(); if (!busy && !jobId) setDragging(true); }}
          onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <div className="upload-icon" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M16 21V5m-6 6 6-6 6 6M6 20v7h20v-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></div>
          <h3>Drop your business cards here</h3>
          <p>JPG, PNG, or WEBP · Up to {settings.max_upload_mb} MB per card</p>
          <button className="button secondary" disabled={busy || !!jobId} onClick={() => picker.current?.click()}>Browse files <span aria-hidden="true">↗</span></button>
          <input className="sr-only" ref={picker} type="file" multiple accept=".jpg,.jpeg,.png,.webp" onChange={onPick} disabled={busy || !!jobId} aria-label="Choose business card images" />
        </div>
        {!!files.length && <div className="file-grid">{files.map(item => <FilePreview key={item.id} file={item.file} disabled={busy || !!jobId}
          onRemove={() => setFiles(current => current.filter(file => file.id !== item.id))} />)}</div>}
        <div className="upload-footer"><p>Images are processed transiently. Server results expire after {Math.round(settings.job_ttl_seconds / 60)} minutes. Export before leaving this page.</p>
          {!jobId ? <button className="button primary" disabled={!files.length || busy || !health?.model_loaded} onClick={() => void start()}>
            {uploading ? <><span className="spinner" /> Uploading cards…</> : <>Extract leads <span aria-hidden="true">→</span></>}
          </button> : <button className="button secondary" disabled={busy || exporting} onClick={() => void clear()}>Start a new batch</button>}
        </div>
      </section>

      {job && <section className="progress-panel" aria-label="Batch progress" aria-live="polite">
        <div><strong>{terminal(job) ? "Batch complete" : "Reading your cards"}</strong><span>{job.processed} of {job.total} processed · {job.successful} successful · {job.failed} failed</span></div>
        <progress value={job.processed} max={job.total} aria-label="Cards processed" />
      </section>}

      <section className="panel results-panel" aria-labelledby="results-heading">
        <div className="section-heading"><div><span className="step-label">02 / REVIEW & EXPORT</span><h2 id="results-heading">Your lead list</h2></div>
          <button className="button primary" disabled={!successCount || busy || exporting} onClick={() => void download()}>{exporting ? "Preparing Excel…" : "Download Excel"} <span aria-hidden="true">↓</span></button></div>
        {successCount ? <><p className="table-hint">Click any field to edit once processing finishes. Blank fields mean information was not visible. AI can make mistakes.</p>
          <ResultsTable results={results} disabled={busy || exporting} onEdit={edit} /></>
          : <div className="empty-state"><div className="empty-lines" aria-hidden="true"><span /><span /><span /></div>
            <h3>{failed.length ? "No readable leads yet" : "A clearer picture of your contacts"}</h3>
            <p>{failed.length ? "Review the errors below and upload clearer images in a new batch." : "Extracted leads will appear here, ready for a quick review and a fresh spreadsheet."}</p></div>}
        {!!failed.length && <div className="failed-list"><h3>{failed.length} {failed.length === 1 ? "card needs" : "cards need"} attention</h3>
          {failed.map(result => <p key={result.index}><strong>{result.source_filename}</strong><span>{result.error}</span></p>)}</div>}
      </section>
      <footer className="page-footer"><span>Business Card Lead Extractor</span><span>Powered by pretrained Qwen · <a href="/qwen-license.txt" target="_blank" rel="noreferrer">Model license</a> · Review before you reach out</span></footer>
    </main>
  </div>;
}
