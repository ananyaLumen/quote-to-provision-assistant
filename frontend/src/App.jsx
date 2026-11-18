import React, { useState } from 'react';
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowLeft, ArrowRight, Bell, BrainCircuit,
  Check, CheckCircle2, ChevronDown, Cloud, Code2,
  FileCheck2, FileJson, FileSearch, FileText, Gauge, LayoutDashboard,
  Menu, Network, Plus, RefreshCw, Settings, ShieldCheck, Sparkles,
  Workflow, X
} from 'lucide-react';
import { API_URL, generateQuote } from './api.js';
import { money, toProposal } from './adapter.js';
import './live.css';

const sampleRequirement = 'We need 10G connectivity between data centres in Mumbai, Chennai and Hyderabad, connected to AWS and Azure with 99.99% SLA, plus a customer portal to monitor bandwidth and raise tickets, integrated with our ServiceNow. Go-live in 5 months.';

const steps = [
  { title: 'Requirement extraction', detail: 'Structuring customer intent and identifying assumptions', icon: FileSearch, timing: 'extractor' },
  { title: 'Past-project retrieval', detail: 'Finding relevant designs, costs and delivery lessons', icon: BrainCircuit, timing: 'retriever' },
  { title: 'Feasibility validation', detail: 'Checking capacity, dependencies and constraints', icon: ShieldCheck, timing: 'validator' },
  { title: 'Parallel solution design', detail: 'Network and software workflows working together', icon: Workflow, timing: 'solutioning' },
  { title: 'Proposal compilation', detail: 'Combining outputs into one engineering proposal', icon: FileCheck2, timing: 'proposal' }
];

const weeks = n => `${Number(Number(n).toFixed(1))} wk`;
const range = (a, b) => (a === b ? money(a) : `${money(a)} – ${money(b)}`);
const Badge = ({ kind, children }) => <span className={`badge ${kind}`}>{children}</span>;

function IconButton({ children, onClick, title }) {
  return <button className="icon-btn" onClick={onClick} title={title}>{children}</button>;
}

function Sidebar({ page, setPage, mobileOpen, setMobileOpen }) {
  const nav = [
    ['Dashboard', LayoutDashboard],
    ['New Proposal', Plus],
    ['Proposal History', FileText],
    ['Settings', Settings]
  ];
  return <>
    {mobileOpen && <div className="mobile-scrim" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="brand">
        <div className="brand-mark"><Workflow size={21}/></div>
        <div><strong>Quote-to-Provision</strong><span>ASSISTANT</span></div>
        <button className="mobile-close" onClick={() => setMobileOpen(false)}><X size={18}/></button>
      </div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>
        {nav.map(([label, Icon]) => (
          <button key={label} className={`nav-item ${page === label ? 'active' : ''}`}
            onClick={() => { setPage(label); setMobileOpen(false); }}>
            <Icon size={17}/><span>{label}</span>{label === 'New Proposal' && <span className="nav-plus">+</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-ai">
          <div className="ai-orb"><Sparkles size={16}/></div>
          <strong>AI workspace</strong>
          <p>Your proposal copilot is ready to help.</p>
          <span className="online-dot">● Online</span>
        </div>
        <div className="profile">
          <div className="avatar">SP</div>
          <div><strong>Project workspace</strong><span>Hackathon prototype</span></div>
          <ChevronDown size={15}/>
        </div>
      </div>
    </aside>
  </>;
}

function Header({ title, setMobileOpen }) {
  return <header className="topbar">
    <div className="topbar-left">
      <button className="mobile-menu" onClick={() => setMobileOpen(true)}><Menu size={20}/></button>
      <div><span className="eyebrow">QUOTE-TO-PROVISION / WORKSPACE</span><h1>{title}</h1></div>
    </div>
    <div className="topbar-actions">
      <span className="environment"><span className="pulse-dot"/> Live pipeline</span>
      <IconButton title="Notifications"><Bell size={17}/></IconButton>
      <div className="avatar">SP</div>
    </div>
  </header>;
}

function RecentCard({ proposal, onOpen }) {
  return <button className="recent-card" onClick={() => onOpen(proposal)}>
    <div className="recent-file"><FileCheck2 size={20}/></div>
    <div className="recent-main"><strong>{proposal.name}</strong><span>{proposal.id} · {proposal.cost} · generated this session</span></div>
    <span className="status-pill"><CheckCircle2 size={13}/> {proposal.status}</span>
    <ArrowRight className="recent-arrow" size={17}/>
  </button>;
}

function Dashboard({ requirement, setRequirement, onGenerate, history, onOpen, setPage }) {
  return <div className="page-content">
    <section className="hero">
      <div className="hero-copy">
        <div className="hero-kicker"><Sparkles size={14}/> YOUR ENGINEERING COPILOT</div>
        <h2>From customer intent<br/><span>to engineering-ready.</span></h2>
        <p>Describe what your customer needs. Let AI shape it into a validated network and software proposal.</p>
        <div className="hero-proof"><span><CheckCircle2 size={15}/> Requirement intelligence</span><span><CheckCircle2 size={15}/> Parallel solution design</span></div>
      </div>
      <div className="hero-visual" aria-label="Abstract AI assistant illustration">
        <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
        <div className="planet"><BrainCircuit size={54}/></div>
        <div className="float-chip chip-a"><Network size={16}/> Network AI</div>
        <div className="float-chip chip-b"><Code2 size={16}/> Software AI</div>
        <div className="float-chip chip-c"><ShieldCheck size={16}/> Validation</div>
        <div className="spark spark-a">✦</div><div className="spark spark-b">✧</div>
      </div>
    </section>

    <section className="section-heading">
      <div><span className="eyebrow">START A WORKFLOW</span><h3>Create a new proposal</h3></div>
      <span className="subtle-label"><span className="pulse-dot"/> Ready for input</span>
    </section>
    <section className="input-panel">
      <div className="input-panel-top"><div className="input-icon"><FileText size={18}/></div><div><strong>Customer requirement</strong><p>Paste a requirement in natural language. Be as detailed as possible.</p></div><span className="optional-tag">NATURAL LANGUAGE</span></div>
      <textarea value={requirement} onChange={e => setRequirement(e.target.value)} placeholder="Example: We need secure 10G connectivity across three locations..."/>
      <div className="input-footer">
        <button className="text-button" onClick={() => setRequirement(sampleRequirement)}><Sparkles size={15}/> Use sample requirement</button>
        <button className="primary-btn" disabled={!requirement.trim()} onClick={onGenerate}><Sparkles size={16}/> Generate proposal <ArrowRight size={16}/></button>
      </div>
    </section>

    {history.length > 0 && <>
      <section className="section-heading recent-heading">
        <div><span className="eyebrow">THIS SESSION</span><h3>Recent proposals</h3></div>
        <button className="text-button" onClick={() => setPage('Proposal History')}>View history <ArrowRight size={15}/></button>
      </section>
      <RecentCard proposal={history[0]} onOpen={onOpen}/>
    </>}
    <div className="disclaimer"><ShieldCheck size={15}/> Prices come from catalog list prices (some catalog entries are mock data) and AI-generated plans are estimates. No live provisioning is performed.</div>
  </div>;
}

function Processing({ progress, timings, error, onRetry, onBack, onFinish }) {
  if (error) {
    return <div className="page-content processing-page">
      <div className="live-error">
        <h3><AlertTriangle size={20}/> We couldn't generate the proposal</h3>
        <p>{error}</p>
        <div className="live-actions">
          <button className="primary-btn" onClick={onRetry}><RefreshCw size={15}/> Try again</button>
          <button className="secondary-btn" onClick={onBack}><ArrowLeft size={15}/> Back to dashboard</button>
        </div>
      </div>
    </div>;
  }
  const finished = progress >= 100;
  return <div className="page-content processing-page">
    <div className="processing-heading">
      <div className="processing-emblem"><div className="emblem-core"><BrainCircuit size={32}/></div><div className="emblem-ring"/></div>
      <span className="hero-kicker"><span className="pulse-dot"/> AI ORCHESTRATION</span>
      <h2>{finished ? 'Your proposal is ready' : 'Building your next solution'}{!finished && <span className="typing-dots">...</span>}</h2>
      <p>{finished ? `Completed in ${Number(timings.total).toFixed(1)} seconds.` : 'Turning customer intent into a structured engineering proposal. This usually takes 10 to 25 seconds.'}</p>
      <div className="progress-track"><div style={{width: `${progress}%`}}/></div>
      <span className="progress-caption">{finished ? 'Workflow complete' : `${Math.round(progress)}% estimated progress`}</span>
    </div>
    <div className="workflow-list">
      {steps.map((step, i) => {
        const Icon = step.icon;
        const done = finished || progress >= (i + 1) * 20;
        const active = !done && progress >= i * 20;
        return <div className={`workflow-step ${done ? 'done' : ''} ${active ? 'working' : ''}`} key={step.title}>
          <div className="workflow-icon"><Icon size={19}/></div>
          <div className="workflow-text"><strong>{step.title}</strong><span>{step.detail}</span></div>
          <div className="workflow-status">{done
            ? <><CheckCircle2 size={16}/> {finished && timings[step.timing] != null ? <span className="step-time">{Number(timings[step.timing]).toFixed(1)}s</span> : 'Complete'}</>
            : active ? <><span className="mini-spinner"/> Working</> : 'Queued'}</div>
        </div>;
      })}
    </div>
    <div className="parallel-work">
      <div className="parallel-card network-card"><div className="parallel-icon"><Network size={19}/></div><div><span>PARALLEL TRACK 01</span><strong>Network Intelligence</strong><p>Topology · BOM · Cost · Provisioning</p></div><div className="track-wave"/></div>
      <div className="parallel-card software-card"><div className="parallel-icon"><Code2 size={19}/></div><div><span>PARALLEL TRACK 02</span><strong>Software Intelligence</strong><p>Architecture · Integrations · Roadmap</p></div><div className="track-wave"/></div>
    </div>
    {finished && <button className="primary-btn centered-btn" onClick={onFinish}>View generated proposal <ArrowRight size={16}/></button>}
    <p className="demo-note">Results come from the live backend pipeline. Progress is estimated while the request runs; the per-step times shown at the end are measured.</p>
  </div>;
}

function Metric({ label, value, note, icon: Icon, tone }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18}/></div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>;
}

function Overview({ proposal, setPage }) {
  const n = proposal.network, s = proposal.software;
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">GENERATED PROPOSAL / {proposal.id}</span><h2>{proposal.name}</h2><p>Generated from your requirement{proposal.totalSeconds ? ` in ${Number(proposal.totalSeconds).toFixed(1)} s` : ''}{proposal.needsReview ? ' · needs human review before it goes to the customer' : ''}</p></div><span className="status-pill"><CheckCircle2 size={13}/> {proposal.status}</span></div>

    <section className="surface-card" style={{marginBottom: 18}}>
      <div className="card-heading"><div><span className="eyebrow">EXECUTIVE SUMMARY</span><h3>What we're proposing</h3></div></div>
      <p className="summary-text">{proposal.summary}</p>
      {proposal.keyPoints.length > 0 && <ul className="summary-points">{proposal.keyPoints.map((k, i) => <li key={i}>{k}</li>)}</ul>}
      <div className="summary-source">{proposal.summarySource === 'llm' ? 'Summary written by AI from the figures below; any figure not in the data is rejected.' : 'Summary generated from a template because the AI summary did not match the data.'}</div>
    </section>

    <div className="metric-grid">
      <Metric label="Estimated cost" value={proposal.cost} note={proposal.costNote} icon={Gauge} tone="blue"/>
      <Metric label="Risk score" value={`${proposal.risk} / 100`} note="100 minus validation confidence" icon={ShieldCheck} tone="green"/>
      <Metric label="Requested timeline" value={proposal.timeline.value} note={proposal.timeline.note} icon={Activity} tone="purple"/>
      <Metric label="Confidence" value={proposal.confidence} note="Share of validation checks passed" icon={BrainCircuit} tone="cyan"/>
    </div>

    <div className="overview-grid">
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">UNDERSTANDING THE ASK</span><h3>Extracted requirements</h3></div><span className="count-pill">{proposal.requirements.length} items</span></div>
        <ul className="check-list">{proposal.requirements.map((r,i)=><li key={i}><Check size={15}/>{r}</li>)}</ul>
      </section>
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">REVIEW BEFORE COMMITTING</span><h3>Assumptions & dependencies</h3></div><span className="warning-pill">{proposal.assumptions.length} to review</span></div>
        <ul className="bullet-list">{proposal.assumptions.slice(0, 6).map((a,i)=><li key={i}>{a}</li>)}</ul>
        {proposal.assumptions.length > 6 && <p className="note-text">+ {proposal.assumptions.length - 6} more in the solution details.</p>}
      </section>
    </div>

    <div className="overview-grid" style={{marginTop: 18}}>
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">FEASIBILITY</span><h3>Validation checks</h3></div><span className="count-pill">{proposal.checks.filter(c => c.status === 'passed').length} of {proposal.checks.length} passed</span></div>
        <ul className="row-list">{proposal.checks.map(c => <li className="row-item" key={c.name}><Badge kind={c.status}>{c.status === 'review' ? 'Review' : c.status}</Badge><div><strong>{c.name}</strong><span className="row-text">{c.message}</span></div></li>)}</ul>
      </section>
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">WHAT COULD GO WRONG</span><h3>Risks</h3></div><span className="count-pill">{proposal.risks.length}</span></div>
        {proposal.risks.length === 0 ? <div className="empty-state">No risks were flagged.</div> :
          <ul className="row-list">{proposal.risks.map((r, i) => <li className="row-item" key={i}><Badge kind={r.level.toLowerCase()}>{r.level}</Badge><div><strong style={{textTransform: 'none'}}>{r.title}</strong>{r.note && <small>Mitigation: {r.note}</small>}</div></li>)}</ul>}
      </section>
    </div>

    {proposal.openQuestions.length > 0 && <section className="surface-card" style={{marginTop: 18}}>
      <div className="card-heading"><div><span className="eyebrow">BEFORE WE CAN FIRM UP THE QUOTE</span><h3>Open questions for the customer</h3></div><span className="count-pill">{proposal.openQuestions.length}</span></div>
      <ul className="bullet-list">{proposal.openQuestions.map((q, i) => <li key={i}>{q}</li>)}</ul>
    </section>}

    <div className="solution-summary-grid">
      <button className="solution-summary network-summary" onClick={() => setPage('Solution Details')}>
        <div className="solution-icon"><Network size={20}/></div><span>NETWORK INTELLIGENCE</span><strong>Connectivity solution</strong><p>{n.summary}</p><em>Explore network design <ArrowRight size={14}/></em>
      </button>
      <button className="solution-summary software-summary" onClick={() => setPage('Solution Details')}>
        <div className="solution-icon"><Code2 size={20}/></div><span>SOFTWARE INTELLIGENCE</span><strong>Software solution</strong><p>{s.summary}</p><em>Explore software plan <ArrowRight size={14}/></em>
      </button>
    </div>
    <div className="bottom-actions"><button className="secondary-btn" onClick={() => setPage('Dashboard')}><ArrowLeft size={15}/> Back to dashboard</button><button className="primary-btn" onClick={() => setPage('Solution Details')}>Explore full proposal <ArrowRight size={16}/></button></div>
  </div>;
}

function NetworkTab({ n }) {
  if (!n.designed) return <section className="surface-card empty-state">{n.summary}</section>;
  const shown = n.locations.slice(0, 3);
  const cost = n.costSummary, range_ = n.costRange;
  return <div className="card-stack">
    <div className="detail-layout">
      <section className="surface-card detail-main"><div className="card-heading"><div><span className="eyebrow">NETWORK INTELLIGENCE</span><h3>{n.locations.length}-site connectivity topology</h3></div></div>
        <div className="topology">
          <div className="topology-line line-one"/><div className="topology-line line-two"/><div className="topology-line line-three"/>
          {shown.map((loc,i)=><div className={`location-node loc-${i}`} key={loc}><div className="node-pulse"><Network size={18}/></div><strong>{loc}</strong><span>site</span></div>)}
          {n.clouds.some(c => /aws|amazon/i.test(c)) && <div className="cloud-node aws"><Cloud size={17}/> AWS</div>}
          {n.clouds.some(c => /azure|microsoft/i.test(c)) && <div className="cloud-node azure"><Cloud size={17}/> Azure</div>}
          {n.locations.length > 3 && <span className="more-sites">+ {n.locations.length - 3} more: {n.locations.slice(3).join(', ')}</span>}
        </div>
        <p className="detail-description">{n.summary}.</p>
        <dl className="kv">
          {n.availability != null && <><dt>Design availability</dt><dd>{n.availability}% (redundant paths assumed independent)</dd></>}
          {n.hub && <><dt>Cloud on-ramp hub</dt><dd>{n.hub} <small>(ranked by free ports; distance not modelled)</small></dd></>}
          {n.leadTimeDays != null && <><dt>Catalog lead time</dt><dd>{n.leadTimeDays} days (excludes site surveys)</dd></>}
        </dl>
      </section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">CATALOG & RATE CARD</span><h3>Bill of materials</h3></div></div>
        <div className="table-wrap"><table><thead><tr><th>Component</th><th className="num">Qty</th><th className="num">Setup</th><th className="num">Monthly</th><th>Source</th></tr></thead>
          <tbody>{n.components.map((row, i)=><tr key={i}><td>{row.name}</td><td className="num">{row.qty}</td><td className="num">{money(row.setup)}</td><td className="num">{money(row.monthly)}</td><td>{row.source}</td></tr>)}
            {cost && <tr className="total"><td>Total</td><td/><td className="num">{money(cost.setup)}</td><td className="num">{money(cost.monthly)}</td><td/></tr>}</tbody></table></div>
        {cost && <p className="note-text">Year one: {money(cost.first_year)} · three-year TCO: {money(cost.three_year_tco)} (list prices).</p>}
      </section>
    </div>
    <div className="two-col">
      {n.alternatives.length > 0 && <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">OTHER COMPLIANT DESIGNS</span><h3>Alternatives considered</h3></div></div>
        <div className="table-wrap"><table><thead><tr><th>Design</th><th className="num">Monthly</th><th className="num">Year one</th></tr></thead><tbody>{n.alternatives.map((a, i)=><tr key={i}><td>{a.design.replace(/\[[^\]]*\]\s*/g, '')}{i === 0 && <> <Badge kind="new">chosen</Badge></>}</td><td className="num">{money(a.monthly)}</td><td className="num">{money(a.first_year)}</td></tr>)}</tbody></table></div>
        {range_ && <p className="note-text">{range_.note}</p>}
      </section>}
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">HOW THIS WAS PRICED</span><h3>Network assumptions</h3></div><span className="count-pill">{n.assumptions.length}</span></div>
        <ul className="bullet-list">{n.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul></section>
    </div>
  </div>;
}

function SoftwareTab({ s }) {
  if (!s.required) return <section className="surface-card empty-state">{s.summary}</section>;
  const e = s.effort;
  return <div className="card-stack">
    <div className="detail-layout">
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">SOFTWARE INTELLIGENCE</span><h3>Proposed technology components</h3></div></div>
        <div className="stack-list">{s.stack.map((x,i)=><div className="stack-item" key={x}><div className="stack-index">0{i+1}</div><strong>{x}</strong><CheckCircle2 size={16}/></div>)}</div>
        <dl className="kv" style={{marginTop: 16}}>
          {s.architecture.frontend && <><dt>Frontend</dt><dd>{s.architecture.frontend}</dd></>}
          {s.architecture.backend && <><dt>Backend</dt><dd>{s.architecture.backend}</dd></>}
          {s.architecture.integration && <><dt>Integration</dt><dd>{s.architecture.integration}</dd></>}
          {s.architecture.hosting && <><dt>Hosting</dt><dd>{s.architecture.hosting}</dd></>}
        </dl></section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">DELIVERY PLANNING</span><h3>Phases and milestones</h3></div></div>
        <div className="roadmap">{s.phases.map((p,i)=><div className="roadmap-item" key={p.name}><div className="roadmap-dot">{i+1}</div><div><strong>{p.name} · {weeks(p.weeks)}</strong><span>{p.milestone}</span></div></div>)}</div></section>
    </div>
    <div className="two-col">
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">ESTIMATE</span><h3>Effort and cost</h3></div></div>
        <dl className="kv">
          <dt>Effort</dt><dd>{e.person_days.minimum} to {e.person_days.maximum} person-days</dd>
          <dt>Duration</dt><dd>{weeks(e.duration_weeks)} (phases run in sequence)</dd>
          <dt>Cost</dt><dd>{range(e.cost.minimum, e.cost.maximum)} at ${e.day_rate_usd}/person-day</dd>
        </dl>
        <p className="note-text">{s.assumptions.join(' ')}</p></section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">INTEGRATIONS</span><h3>Systems to connect</h3></div></div>
        <ul className="row-list">{s.integrations.map((x, i) => <li className="row-item" key={i}><div><strong style={{textTransform: 'none'}}>{x.system}</strong><span className="row-text">{x.purpose}</span><small>{x.approach}</small></div></li>)}</ul></section>
    </div>
    <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">DATABASE & DATA INTEGRATION</span><h3>{s.database.engine}</h3><p className="muted">{s.database.rationale}</p></div></div>
      <div className="table-wrap"><table><thead><tr><th>Table</th><th>Status</th><th>Purpose</th><th>Key fields</th></tr></thead>
        <tbody>{s.database.entities.map(en => <tr key={en.name}><td>{en.name}</td><td><Badge kind={en.existing_table ? 'existing' : 'new'}>{en.existing_table ? 'existing' : 'new'}</Badge></td><td>{en.purpose}</td><td>{(en.key_fields || []).join(', ')}</td></tr>)}</tbody></table></div>
      {s.database.data_integration?.length > 0 && <ul className="bullet-list" style={{marginTop: 14}}>{s.database.data_integration.map((d, i) => <li key={i}>{d}</li>)}</ul>}
    </section>
  </div>;
}

function RoadmapTab({ proposal }) {
  const c = proposal.costs, r = proposal.roadmap, i = r?.integrated;
  return <div className="card-stack">
    <div className="two-col">
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">COMMERCIALS</span><h3>First-year cost</h3></div></div>
        {!c.total_first_year ? <div className="empty-state">{proposal.commercialNote}</div> :
          <div className="table-wrap"><table><thead><tr><th>Item</th><th className="num">Minimum</th><th className="num">Maximum</th></tr></thead><tbody>
            <tr><td>Network (setup + 12 months)</td><td className="num">{money(c.network.first_year_minimum)}</td><td className="num">{money(c.network.first_year_maximum)}</td></tr>
            <tr><td>Software build</td><td className="num">{money(c.software.minimum)}</td><td className="num">{money(c.software.maximum)}</td></tr>
            <tr className="total"><td>Total</td><td className="num">{money(c.total_first_year.minimum)}</td><td className="num">{money(c.total_first_year.maximum)}</td></tr></tbody></table></div>}
        <p className="note-text">{c.basis}</p></section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">INTEGRATED DELIVERY</span><h3>Roadmap summary</h3></div></div>
        {r.tracks.length === 0 ? <div className="empty-state">No roadmap until sites and bandwidth are confirmed.</div> : <dl className="kv">
          <dt>Computed duration</dt><dd>{i.total_months} months (lower bound)</dd>
          <dt>Critical path</dt><dd>{i.critical_path}</dd>
          {i.requested_months && <><dt>Requested</dt><dd>{i.requested_months} months · {i.fits_requested_timeline === false ? 'at risk' : i.fits_requested_timeline ? 'within plan' : 'not confirmed'}</dd></>}
          {i.benchmark && <><dt>Benchmark</dt><dd>{i.benchmark}</dd></>}
        </dl>}
        {r.notes.map((note, k) => <p className="note-text" key={k}>{note}</p>)}</section>
    </div>
    {r.tracks.map(t => <section className="surface-card" key={t.name}><div className="card-heading"><div><span className="eyebrow">TRACK</span><h3>{t.name}</h3></div><span className="count-pill">{weeks(t.duration_weeks)}</span></div>
      <div className="roadmap">{t.steps.map((st, k) => <div className="roadmap-item" key={st.name}><div className="roadmap-dot">{k+1}</div><div><strong>{st.name}</strong><span>Week {st.start_week} to {st.end_week}{st.milestone ? ` · ${st.milestone}` : ''}</span></div></div>)}</div></section>)}
  </div>;
}

function SolutionDetails({ proposal, tab, setTab, setPage }) {
  const tabs = ['Network Design','Software Plan','Roadmap & Cost','Similar Projects','Provisioning'];
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">ENGINEERING OUTPUT / {proposal.id}</span><h2>Solution details</h2><p>Explore the outputs from both intelligence tracks.</p></div>
      <button className="primary-btn" onClick={() => setPage('Export Proposal')}>Export proposal <ArrowRight size={16}/></button></div>
    <div className="tabs">{tabs.map(t=><button key={t} className={tab===t?'selected':''} onClick={()=>setTab(t)}>{t}</button>)}</div>
    {tab === 'Network Design' && <NetworkTab n={proposal.network}/>}
    {tab === 'Software Plan' && <SoftwareTab s={proposal.software}/>}
    {tab === 'Roadmap & Cost' && <RoadmapTab proposal={proposal}/>}
    {tab === 'Similar Projects' && <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">RETRIEVAL</span><h3>Relevant past-work matches</h3><p>Ranked by semantic similarity to your requirement. Scores are close together because the project history is small.</p></div></div>
      {proposal.similar.length === 0 ? <div className="empty-state">No similar projects were found.</div> :
        <div className="similar-list">{proposal.similar.map(p=><div className="similar-item" key={p.name}><div className="similar-icon"><FileSearch size={18}/></div><div><strong>{p.name} <Badge kind={p.source === 'real' ? 'real' : 'synthetic'}>{p.source}</Badge></strong><span>{p.months ? `${p.months} months · ` : ''}{p.lesson ? `Lesson learned: ${p.lesson}` : 'No lessons recorded.'}</span></div><div className="similar-score">{p.score}<small>similarity</small></div></div>)}</div>}</section>}
    {tab === 'Provisioning' && <div className="card-stack"><section className="surface-card"><div className="card-heading"><div><span className="eyebrow">STRUCTURED OUTPUT</span><h3>Provisioning payload</h3><p>Draft that validates against the provisioning schema. Customer fields are placeholders.</p></div><span className="warning-pill">{proposal.provisioningReady ? 'Ready' : 'Not ready'}</span></div>
      {proposal.provisioningJson ? <pre className="json-view">{JSON.stringify(proposal.provisioningJson, null, 2)}</pre> : <div className="empty-state">{proposal.provisioningNote}</div>}
      <div className="disclaimer"><ShieldCheck size={15}/> This prototype does not connect to network devices or provision services.</div></section>
      {proposal.network.blockers.length > 0 && <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">BEFORE SUBMISSION</span><h3>What blocks provisioning</h3></div></div><ul className="bullet-list">{proposal.network.blockers.map((b, i) => <li key={i}>{b}</li>)}</ul></section>}</div>}
  </div>;
}

function Export({ proposal }) {
  const json = JSON.stringify(proposal.raw, null, 2);
  const download = (name, content, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  };
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">FINAL OUTPUT</span><h2>Export proposal</h2><p>Review the generated summary and export it.</p></div><span className="status-pill"><CheckCircle2 size={13}/> {proposal.needsReview ? 'Needs review' : 'Ready for review'}</span></div>
    <div className="export-layout">
      <section className="surface-card export-preview">
        <div className="preview-toolbar"><span><FileText size={16}/> PROPOSAL PREVIEW</span><span className="mock-tag">DRAFT</span></div>
        <div className="preview-page"><div className="preview-brand"><div className="brand-mark"><Workflow size={17}/></div><span>QUOTE-TO-PROVISION ASSISTANT</span></div><div className="preview-rule"/>
          <span className="eyebrow">ENGINEERING PROPOSAL / {proposal.id}</span><h2>{proposal.name}</h2><p>{proposal.status} · confidence {proposal.confidence}</p>
          <div className="preview-stats"><div><small>FIRST-YEAR COST</small><strong>{proposal.cost}</strong></div><div><small>RISK SCORE</small><strong>{proposal.risk}/100</strong></div><div><small>REQUESTED</small><strong>{proposal.timeline.value}</strong></div></div>
          <h3>Summary</h3><p>{proposal.summary}</p>
          <h3>Network</h3><p>{proposal.network.summary}</p>
          <h3>Software</h3><p>{proposal.software.summary}</p>
          {proposal.openQuestions.length > 0 && <><h3>Open questions</h3><ul>{proposal.openQuestions.map((q, i) => <li key={i}>{q}</li>)}</ul></>}
          <div className="preview-footer">Planning estimate from catalog list prices · Not a commercial quote · No live provisioning</div>
        </div>
      </section>
      <section className="surface-card export-options"><span className="eyebrow">DOWNLOAD ARTEFACTS</span><h3>Take your proposal further</h3><p>Export the generated proposal for review.</p>
        <button className="export-option" onClick={() => window.print()}><div className="export-icon pdf"><FileText size={21}/></div><div><strong>Print / Save as PDF</strong><span>Open the browser print dialog</span></div><ArrowDownToLine size={17}/></button>
        <button className="export-option" onClick={() => download(`${proposal.id}.json`, json, 'application/json')}><div className="export-icon js"><FileJson size={21}/></div><div><strong>Download full result JSON</strong><span>Requirement, validation, network, software and proposal</span></div><ArrowDownToLine size={17}/></button>
        {proposal.provisioningJson && <button className="export-option" onClick={() => download(`${proposal.id}-provisioning.json`, JSON.stringify(proposal.provisioningJson, null, 2), 'application/json')}><div className="export-icon js"><FileJson size={21}/></div><div><strong>Download provisioning payload</strong><span>Draft in the provisioning schema format</span></div><ArrowDownToLine size={17}/></button>}
        <div className="disclaimer"><ShieldCheck size={15}/> Figures are planning estimates, not a commercial quote.</div>
      </section>
    </div>
  </div>;
}

export default function App() {
  const [page, setPage] = useState('Dashboard');
  const [requirement, setRequirement] = useState(sampleRequirement);
  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const [progress, setProgress] = useState(0);
  const [timings, setTimings] = useState({});
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('Network Design');
  const [mobileOpen, setMobileOpen] = useState(false);

  const generate = async () => {
    setError(null);
    setTimings({});
    setProgress(3);
    setPage('AI Processing');
    // The pipeline is one request, so progress is an estimate that eases towards 92% until the response arrives.
    const timer = setInterval(() => setProgress(p => Math.min(92, p + Math.max(0.6, (92 - p) * 0.05))), 400);
    try {
      const state = await generateQuote(requirement);
      const proposal = toProposal(state);
      setTimings(state.timings || {});
      setCurrent(proposal);
      setHistory(h => [proposal, ...h]);
      setProgress(100);
    } catch (e) {
      setError(e.message || 'Something went wrong.');
    } finally {
      clearInterval(timer);
    }
  };

  const open = proposal => { setCurrent(proposal); setTab('Network Design'); setPage('Proposal Overview'); };

  const titles = {
    'Dashboard': 'Dashboard',
    'New Proposal': 'New proposal',
    'AI Processing': 'AI processing',
    'Proposal Overview': 'Proposal overview',
    'Solution Details': 'Solution details',
    'Proposal History': 'Proposal history',
    'Settings': 'Workspace settings',
    'Export Proposal': 'Export proposal'
  };

  const needsProposal = ['Proposal Overview', 'Solution Details', 'Export Proposal'];

  const renderPage = () => {
    if (needsProposal.includes(page) && !current) {
      return <div className="page-content"><div className="surface-card empty-state">No proposal yet. Generate one from the dashboard.<div style={{marginTop: 16}}><button className="primary-btn" onClick={() => setPage('Dashboard')}>Go to dashboard</button></div></div></div>;
    }
    if (page === 'Dashboard' || page === 'New Proposal') return <Dashboard requirement={requirement} setRequirement={setRequirement} onGenerate={generate} history={history} onOpen={open} setPage={setPage}/>;
    if (page === 'AI Processing') return <Processing progress={progress} timings={timings} error={error} onRetry={generate} onBack={() => setPage('Dashboard')} onFinish={() => { setTab('Network Design'); setPage('Proposal Overview'); }}/>;
    if (page === 'Proposal Overview') return <Overview proposal={current} setPage={setPage}/>;
    if (page === 'Solution Details') return <SolutionDetails proposal={current} tab={tab} setTab={setTab} setPage={setPage}/>;
    if (page === 'Export Proposal') return <Export proposal={current}/>;
    if (page === 'Proposal History') return <div className="page-content"><div className="proposal-title-row"><div><span className="eyebrow">WORKSPACE</span><h2>Proposal history</h2><p>Proposals generated in this browser session. They are not saved on the server yet.</p></div></div>
      {history.length === 0 ? <div className="surface-card empty-state">Nothing generated yet.</div> : <div className="card-stack">{history.map(p => <RecentCard key={p.id} proposal={p} onOpen={open}/>)}</div>}</div>;
    return <div className="page-content"><div className="proposal-title-row"><div><span className="eyebrow">WORKSPACE</span><h2>Workspace settings</h2><p>Connection to the backend.</p></div></div><div className="surface-card"><h3>API</h3><dl className="kv"><dt>Backend URL</dt><dd>{API_URL}</dd></dl><p className="note-text">Set VITE_API_URL in the frontend environment to point at a different backend, then restart the dev server. The backend is internal-network only because it calls the company LLM gateway.</p></div></div>;
  };

  return <div className="app-shell">
    <Sidebar page={page} setPage={setPage} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}/>
    <main className="main-area">
      <Header title={titles[page] || page} setMobileOpen={setMobileOpen}/>
      {renderPage()}
      <footer className="app-footer"><span>QUOTE-TO-PROVISION ASSISTANT</span><span>Hackathon prototype · Estimates are planning figures</span></footer>
    </main>
  </div>;
}
