import React, { useMemo, useState } from 'react';
import {
  Activity, ArrowDownToLine, ArrowLeft, ArrowRight, Bell, BrainCircuit,
  Check, CheckCircle2, ChevronDown, CircleHelp, Cloud, Code2, Cpu,
  FileCheck2, FileJson, FileSearch, FileText, Gauge, LayoutDashboard,
  Menu, Network, Plus, Search, Settings, ShieldCheck, Sparkles,
  Workflow, X, Zap
} from 'lucide-react';

const sampleRequirement = 'We need 10G connectivity between data centres in Mumbai, Chennai and Hyderabad, connected to AWS and Azure with 99.99% SLA, plus a customer portal to monitor bandwidth and raise tickets, integrated with our ServiceNow. Go-live in 5 months.';

const steps = [
  { title: 'Requirement extraction', detail: 'Structuring customer intent and identifying assumptions', icon: FileSearch },
  { title: 'Past-project retrieval', detail: 'Finding relevant designs, costs and delivery lessons', icon: BrainCircuit },
  { title: 'Feasibility validation', detail: 'Checking capacity, dependencies and constraints', icon: ShieldCheck },
  { title: 'Parallel solution design', detail: 'Network and software workflows working together', icon: Workflow },
  { title: 'Proposal compilation', detail: 'Combining outputs into one engineering proposal', icon: FileCheck2 }
];

const initialProposal = {
  id: 'QTP-2026-0142',
  name: 'Meridian multi-cloud expansion',
  cost: '₹48.6L',
  risk: 18,
  timeline: '5 months',
  confidence: '92%',
  status: 'Validated with assumptions',
  requirements: [
    '10G connectivity between Mumbai, Chennai and Hyderabad',
    'AWS and Azure cloud connectivity',
    '99.99% availability SLA',
    'Customer portal for bandwidth monitoring',
    'Ticket creation integrated with ServiceNow',
    'Target go-live in 5 months'
  ],
  assumptions: [
    'Diverse fibre routes are available at all three locations.',
    'Cloud connectivity subscriptions are provisioned by the customer.',
    'ServiceNow API access and credentials will be provided.'
  ],
  risks: [
    { level: 'Medium', title: 'Route diversity confirmation', note: 'Physical path diversity needs carrier confirmation.' },
    { level: 'Low', title: 'ServiceNow integration dependency', note: 'Requires API access and test environment.' }
  ],
  network: {
    summary: 'Three-site 10G interconnected network with dual-cloud connectivity.',
    locations: ['Mumbai', 'Chennai', 'Hyderabad'],
    components: [
      ['10G connectivity links', '3', 'Mock catalog'],
      ['Edge network devices', '3', 'Mock catalog'],
      ['Cloud connectivity endpoints', '2', 'Mock catalog'],
      ['Monitoring integration', '1', 'Mock catalog']
    ]
  },
  software: {
    stack: ['React customer portal', 'FastAPI services', 'PostgreSQL database', 'ServiceNow REST integration'],
    phases: [
      ['Discovery & design', 'Month 1'],
      ['Network and platform foundation', 'Months 2–3'],
      ['Portal and integrations', 'Months 3–4'],
      ['Testing and go-live', 'Month 5']
    ]
  },
  similar: [
    { name: 'Multi-city enterprise WAN', score: '89%', lesson: 'Plan carrier route diversity early.' },
    { name: 'Hybrid cloud connectivity', score: '84%', lesson: 'Validate cloud handoff and bandwidth ownership.' },
    { name: 'Customer network portal', score: '78%', lesson: 'Confirm ticketing API scope before build.' }
  ]
};

function mapQuoteStateToProposal(data) {
  const requirement = data.requirement || {};
  const validation = data.validation || {};
  const network = data.network || {};
  const software = data.software || {};

  const requirements = [
    requirement.bandwidth
      ? `${requirement.bandwidth} connectivity between ${(requirement.sites || []).join(", ")}`
      : null,

    (requirement.clouds || []).length
      ? `${requirement.clouds.join(" and ")} cloud connectivity`
      : null,

    requirement.sla
      ? `${requirement.sla} availability SLA`
      : null,

    ...(requirement.integrations || []).map(
      (integration) => `${integration} integration`
    ),

    requirement.timeline
      ? `Target go-live in ${requirement.timeline}`
      : null,
  ].filter(Boolean);

  const risks = (validation.risks || []).map((risk) => ({
    level: risk.severity
      ? risk.severity.charAt(0).toUpperCase() + risk.severity.slice(1)
      : "Unknown",
    title: risk.description || "Validation risk",
    note: risk.description || "",
  }));

  const networkComponents = (network.bom || []).map((item) => [
    item.item || "Network component",
    String(item.quantity ?? ""),
    "Stub solution",
  ]);

  const similar = (data.similar_projects || []).map((project) => ({
    name: project.summary || project.project_id || "Similar project",
    score:
      typeof project.similarity === "number"
        ? `${Math.round(project.similarity * 100)}%`
        : "N/A",
    lesson:
      (project.technologies || []).length > 0
        ? `Relevant technologies: ${project.technologies.join(", ")}`
        : "Reference project",
  }));

  return {
    id: data.request_id || "Pending",

    name:
      data.proposal?.title ||
      "Quote-to-Provision Solution Proposal",

    cost:
      network.cost_range?.minimum || network.cost_range?.maximum
        ? `${network.cost_range.currency || "USD"} ${
            network.cost_range.minimum ?? 0
          }–${network.cost_range.maximum ?? 0}`
        : "Pricing pending",

    risk: risks.length,

    timeline: requirement.timeline || "TBD",

    confidence:
      typeof validation.confidence === "number"
        ? `${Math.round(validation.confidence * 100)}%`
        : "N/A",

    status:
      validation.feasible === true
        ? "Validated with assumptions"
        : "Requires review",

    requirements,

    assumptions: data.assumptions || [],

    risks,

    network: {
      summary:
        network.recommended_solution ||
        "Network solution pending",

      locations:
        network.architecture?.sites || requirement.sites || [],

      components: networkComponents,
    },

    software: {
      stack: software.stack || [],

      phases: [
        ["Discovery & design", "Month 1"],
        ["Network and platform foundation", "Months 2–3"],
        ["Portal and integrations", "Months 3–4"],
        ["Testing and go-live", requirement.timeline || "TBD"],
      ],
    },

    similar,
  };
}

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
          <div><strong>Project workspace</strong><span>Hackathon demo</span></div>
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
      <span className="environment"><span className="pulse-dot"/> Demo environment</span>
      <IconButton title="Notifications"><Bell size={17}/></IconButton>
      <div className="avatar">SP</div>
    </div>
  </header>;
}

function Dashboard({ requirement, setRequirement, onGenerate, proposal, setPage }) {
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

    <section className="section-heading recent-heading">
      <div><span className="eyebrow">WORKSPACE ACTIVITY</span><h3>Recent proposals</h3></div>
      <button className="text-button" onClick={() => setPage('Proposal History')}>View history <ArrowRight size={15}/></button>
    </section>
    <button className="recent-card" onClick={() => setPage('Proposal Overview')}>
      <div className="recent-file"><FileCheck2 size={20}/></div>
      <div className="recent-main"><strong>{proposal.name}</strong><span>{proposal.id} · Updated just now · Demo data</span></div>
      <span className="status-pill"><CheckCircle2 size={13}/> {proposal.status}</span>
      <ArrowRight className="recent-arrow" size={17}/>
    </button>
    <div className="disclaimer"><ShieldCheck size={15}/> Demo workspace uses illustrative synthetic project data and mock catalog values. No live provisioning is performed.</div>
  </div>;
}

function Processing({ progress, onFinish }) {
  return <div className="page-content processing-page">
    <div className="processing-heading">
      <div className="processing-emblem"><div className="emblem-core"><BrainCircuit size={32}/></div><div className="emblem-ring"/></div>
      <span className="hero-kicker"><span className="pulse-dot"/> AI ORCHESTRATION</span>
      <h2>Building your next solution<span className="typing-dots">...</span></h2>
      <p>Turning customer intent into a structured engineering proposal.</p>
      <div className="progress-track"><div style={{width: `${progress}%`}}/></div>
      <span className="progress-caption">{Math.min(progress,100)}% workflow progress</span>
    </div>
    <div className="workflow-list">
      {steps.map((step, i) => {
        const Icon = step.icon;
        const done = progress >= (i + 1) * 20;
        const active = !done && progress >= i * 20;
        return <div className={`workflow-step ${done ? 'done' : ''} ${active ? 'working' : ''}`} key={step.title}>
          <div className="workflow-icon"><Icon size={19}/></div>
          <div className="workflow-text"><strong>{step.title}</strong><span>{step.detail}</span></div>
          <div className="workflow-status">{done ? <><CheckCircle2 size={16}/> Complete</> : active ? <><span className="mini-spinner"/> Working</> : 'Queued'}</div>
        </div>;
      })}
    </div>
    <div className="parallel-work">
      <div className="parallel-card network-card"><div className="parallel-icon"><Network size={19}/></div><div><span>PARALLEL TRACK 01</span><strong>Network Intelligence</strong><p>Topology · BOM · Cost · Provisioning</p></div><div className="track-wave"/></div>
      <div className="parallel-card software-card"><div className="parallel-icon"><Code2 size={19}/></div><div><span>PARALLEL TRACK 02</span><strong>Software Intelligence</strong><p>Architecture · Integrations · Roadmap</p></div><div className="track-wave"/></div>
    </div>
    {progress >= 100 && <button className="primary-btn centered-btn" onClick={onFinish}>View generated proposal <ArrowRight size={16}/></button>}
    <p className="demo-note">This is a simulated frontend workflow. Connect your orchestration API to display real execution states.</p>
  </div>;
}

function Metric({ label, value, note, icon: Icon, tone }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18}/></div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>;
}

function Overview({ proposal, setPage }) {
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">GENERATED PROPOSAL / {proposal.id}</span><h2>{proposal.name}</h2><p>Customer solution brief · Demo data · Generated moments ago</p></div><span className="status-pill"><CheckCircle2 size={13}/> {proposal.status}</span></div>
    <div className="metric-grid">
      <Metric label="Estimated cost" value={proposal.cost} note="Illustrative mock catalog estimate" icon={Gauge} tone="blue"/>
      <Metric label="Risk score" value={`${proposal.risk} / 100`} note="Illustrative risk assessment" icon={ShieldCheck} tone="green"/>
      <Metric label="Delivery timeline" value={proposal.timeline} note="Planning estimate" icon={Activity} tone="purple"/>
      <Metric label="Confidence" value={proposal.confidence} note="Illustrative model confidence" icon={BrainCircuit} tone="cyan"/>
    </div>
    <div className="overview-grid">
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">UNDERSTANDING THE ASK</span><h3>Extracted requirements</h3></div><span className="count-pill">{proposal.requirements.length} items</span></div>
        <ul className="check-list">{proposal.requirements.map((r,i)=><li key={i}><Check size={15}/>{r}</li>)}</ul>
      </section>
      <section className="surface-card">
        <div className="card-heading"><div><span className="eyebrow">REVIEW BEFORE COMMITTING</span><h3>Assumptions & dependencies</h3></div><span className="warning-pill">Review</span></div>
        <ul className="bullet-list">{proposal.assumptions.map((a,i)=><li key={i}>{a}</li>)}</ul>
      </section>
    </div>
    <div className="solution-summary-grid">
      <button className="solution-summary network-summary" onClick={() => setPage('Solution Details')}>
        <div className="solution-icon"><Network size={20}/></div><span>NETWORK INTELLIGENCE</span><strong>Connectivity solution</strong><p>{proposal.network.summary}</p><em>Explore network design <ArrowRight size={14}/></em>
      </button>
      <button className="solution-summary software-summary" onClick={() => setPage('Solution Details')}>
        <div className="solution-icon"><Code2 size={20}/></div><span>SOFTWARE INTELLIGENCE</span><strong>Application delivery plan</strong><p>Portal, backend, database, ServiceNow integration and phased roadmap.</p><em>Explore software plan <ArrowRight size={14}/></em>
      </button>
    </div>
    <div className="bottom-actions"><button className="secondary-btn" onClick={() => setPage('Dashboard')}><ArrowLeft size={15}/> Back to dashboard</button><button className="primary-btn" onClick={() => setPage('Solution Details')}>Explore full proposal <ArrowRight size={16}/></button></div>
  </div>;
}

function SolutionDetails({ proposal, tab, setTab }) {
  const tabs = ['Network Design','Software Plan','Similar Projects','Provisioning'];
  const json = useMemo(() => JSON.stringify({
    proposal_id: proposal.id,
    environment: 'DEMO_ONLY',
    provisioning_status: 'NOT_DEPLOYED',
    locations: proposal.network.locations,
    connectivity: { bandwidth: '10G', sla: '99.99%' },
    cloud: ['AWS','Azure'],
    integrations: ['ServiceNow'],
    note: 'Illustrative configuration only. No live provisioning.'
  }, null, 2), [proposal]);
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">ENGINEERING OUTPUT</span><h2>Solution details</h2><p>Explore the outputs from both intelligence tracks.</p></div><span className="status-pill"><CheckCircle2 size={13}/> Demo proposal</span></div>
    <div className="tabs">{tabs.map(t=><button key={t} className={tab===t?'selected':''} onClick={()=>setTab(t)}>{t}</button>)}</div>
    {tab === 'Network Design' && <div className="detail-layout">
      <section className="surface-card detail-main"><div className="card-heading"><div><span className="eyebrow">NETWORK INTELLIGENCE</span><h3>Multi-city connectivity topology</h3></div><span className="mock-tag">Illustrative</span></div>
        <div className="topology">
          <div className="topology-line line-one"/><div className="topology-line line-two"/><div className="topology-line line-three"/>
          {proposal.network.locations.map((loc,i)=><div className={`location-node loc-${i}`} key={loc}><div className="node-pulse"><Network size={18}/></div><strong>{loc}</strong><span>10G site</span></div>)}
          <div className="cloud-node aws"><Cloud size={17}/> AWS</div><div className="cloud-node azure"><Cloud size={17}/> Azure</div>
        </div>
        <p className="detail-description">{proposal.network.summary} Final route design requires carrier feasibility confirmation.</p>
      </section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">MOCK CATALOG</span><h3>Bill of materials</h3></div></div>
        <div className="table-wrap"><table><thead><tr><th>Component</th><th>Qty</th><th>Source</th></tr></thead><tbody>{proposal.network.components.map(row=><tr key={row[0]}><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>)}</tbody></table></div>
      </section>
    </div>}
    {tab === 'Software Plan' && <div className="detail-layout">
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">SOFTWARE INTELLIGENCE</span><h3>Proposed technology components</h3></div></div><div className="stack-list">{proposal.software.stack.map((s,i)=><div className="stack-item" key={s}><div className="stack-index">0{i+1}</div><strong>{s}</strong><CheckCircle2 size={16}/></div>)}</div></section>
      <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">DELIVERY PLANNING</span><h3>Indicative roadmap</h3></div></div><div className="roadmap">{proposal.software.phases.map((p,i)=><div className="roadmap-item" key={p[0]}><div className="roadmap-dot">{i+1}</div><div><strong>{p[0]}</strong><span>{p[1]}</span></div></div>)}</div></section>
    </div>}
    {tab === 'Similar Projects' && <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">RAG RETRIEVAL</span><h3>Relevant past-work matches</h3><p>Illustrative synthetic project records for the demo.</p></div></div><div className="similar-list">{proposal.similar.map((p,i)=><div className="similar-item" key={p.name}><div className="similar-icon"><FileSearch size={18}/></div><div><strong>{p.name}</strong><span>Lesson learned: {p.lesson}</span></div><div className="similar-score">{p.score}<small>similarity</small></div></div>)}</div></section>}
    {tab === 'Provisioning' && <section className="surface-card"><div className="card-heading"><div><span className="eyebrow">STRUCTURED OUTPUT</span><h3>Provisioning configuration</h3><p>Example JSON payload prepared for downstream review.</p></div><span className="warning-pill">Not deployed</span></div><pre className="json-view">{json}</pre><div className="disclaimer"><ShieldCheck size={15}/> Mock JSON only. This prototype does not connect to network devices or provision services.</div></section>}
  </div>;
}

function Export({ proposal }) {
  const json = JSON.stringify({ proposal, note: 'Synthetic demo content; not a live quote or provisioning instruction.' }, null, 2);
  const download = (name, content, type) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = name; a.click();
    URL.revokeObjectURL(url);
  };
  return <div className="page-content">
    <div className="proposal-title-row"><div><span className="eyebrow">FINAL OUTPUT</span><h2>Export proposal</h2><p>Review the generated summary and export demo artefacts.</p></div><span className="status-pill"><CheckCircle2 size={13}/> Ready for review</span></div>
    <div className="export-layout">
      <section className="surface-card export-preview">
        <div className="preview-toolbar"><span><FileText size={16}/> PROPOSAL PREVIEW</span><span className="mock-tag">DEMO</span></div>
        <div className="preview-page"><div className="preview-brand"><div className="brand-mark"><Workflow size={17}/></div><span>QUOTE-TO-PROVISION ASSISTANT</span></div><div className="preview-rule"/>
          <span className="eyebrow">ENGINEERING PROPOSAL / {proposal.id}</span><h2>{proposal.name}</h2><p>Customer solution proposal · Illustrative demo output</p>
          <div className="preview-stats"><div><small>ESTIMATED COST</small><strong>{proposal.cost}</strong></div><div><small>RISK SCORE</small><strong>{proposal.risk}/100</strong></div><div><small>TIMELINE</small><strong>{proposal.timeline}</strong></div></div>
          <h3>Solution summary</h3><p>{proposal.network.summary}</p><p>Software delivery includes {proposal.software.stack.join(', ')}.</p>
          <div className="preview-check"><CheckCircle2 size={16}/> Validation summary available for review</div>
          <div className="preview-footer">Synthetic demo data · Not a commercial quote · No live provisioning</div>
        </div>
      </section>
      <section className="surface-card export-options"><span className="eyebrow">DOWNLOAD ARTEFACTS</span><h3>Take your proposal further</h3><p>Export the illustrative proposal data for review or use in your demo.</p>
        <button className="export-option" onClick={() => window.print()}><div className="export-icon pdf"><FileText size={21}/></div><div><strong>Print / Save as PDF</strong><span>Open the browser print dialog</span></div><ArrowDownToLine size={17}/></button>
        <button className="export-option" onClick={() => download(`${proposal.id}.json`, json, 'application/json')}><div className="export-icon js"><FileJson size={21}/></div><div><strong>Download proposal JSON</strong><span>Structured proposal data</span></div><ArrowDownToLine size={17}/></button>
        <div className="disclaimer"><ShieldCheck size={15}/> Exported values are sample data. Replace with backend-generated results before presenting them as actual estimates.</div>
      </section>
    </div>
  </div>;
}

export default function App() {
  const [page, setPage] = useState('Dashboard');
  const [requirement, setRequirement] = useState(sampleRequirement);
  const [quoteResult, setQuoteResult] = useState(null);
  const [apiError, setApiError] = useState("");
  const [proposal, setProposal] = useState(initialProposal);
  const [progress, setProgress] = useState(0);
  const [tab, setTab] = useState('Network Design');
  const [mobileOpen, setMobileOpen] = useState(false);

  const generate = async () => {
  if (!requirement.trim()) return;

  setApiError("");
  setProgress(10);
  setPage("AI Processing");

  try {
    setProgress(30);

    const response = await fetch("http://127.0.0.1:8000/quote", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        requirement_text: requirement,
      }),
    });

    setProgress(70);

    if (!response.ok) {
      throw new Error(`Quote API failed with status ${response.status}`);
    }

    const data = await response.json();

    setQuoteResult(data);

    const mappedProposal = mapQuoteStateToProposal(data);
    setProposal(mappedProposal);

setProgress(100);

    setTimeout(() => {
      setPage("Proposal Overview");
    }, 400);
  } catch (error) {
    console.error("Quote generation failed:", error);
    setApiError(error.message);
    setProgress(0);
    setPage("Dashboard");
  }
};

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

  const renderPage = () => {
    if (page === 'Dashboard' || page === 'New Proposal') return <Dashboard requirement={requirement} setRequirement={setRequirement} onGenerate={generate} proposal={proposal} setPage={setPage}/>;
    if (page === 'AI Processing') return <Processing progress={progress} onFinish={() => setPage('Proposal Overview')}/>;
    if (page === 'Proposal Overview') return <Overview proposal={proposal} setPage={setPage}/>;
    if (page === 'Solution Details') return <SolutionDetails proposal={proposal} tab={tab} setTab={setTab}/>;
    if (page === 'Export Proposal') return <Export proposal={proposal}/>;
    if (page === 'Proposal History') return <div className="page-content"><div className="proposal-title-row"><div><span className="eyebrow">WORKSPACE</span><h2>Proposal history</h2><p>Your recent generated proposals.</p></div></div><button className="recent-card" onClick={() => setPage('Proposal Overview')}><div className="recent-file"><FileCheck2 size={20}/></div><div className="recent-main"><strong>{proposal.name}</strong><span>{proposal.id} · Synthetic demo record</span></div><span className="status-pill">Demo</span><ArrowRight size={17}/></button></div>;
    return <div className="page-content"><div className="proposal-title-row"><div><span className="eyebrow">WORKSPACE</span><h2>Workspace settings</h2><p>Settings will be connected to your team environment later.</p></div></div><div className="surface-card"><h3>Demo configuration</h3><p className="muted">This frontend currently runs locally with illustrative data. API configuration will be added during backend integration.</p></div></div>;
  };

  return <div className="app-shell">
    <Sidebar page={page} setPage={setPage} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}/>
    <main className="main-area">
      <Header title={titles[page] || page} setMobileOpen={setMobileOpen}/>
      {renderPage()}
      <footer className="app-footer"><span>QUOTE-TO-PROVISION ASSISTANT</span><span>Hackathon prototype · Demo data only</span></footer>
    </main>
  </div>;
}
