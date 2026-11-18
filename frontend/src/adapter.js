// Maps the backend QuoteState onto the shapes the UI components render.

export const VERDICTS = {
  feasible: 'Feasible',
  feasible_with_conditions: 'Feasible with conditions',
  not_feasible: 'Not feasible',
  insufficient_information: 'More information needed',
};

const clean = text => String(text ?? '').replace(/\[[^\]]*\]\s*/g, '').trim();
const tagOf = text => (/\[(REAL|MOCK|SYNTHETIC)[^\]]*\]/i.exec(String(text ?? '')) || [])[1]?.toLowerCase() || null;
const clip = (text, n) => (text.length > n ? `${text.slice(0, n - 1).trimEnd()}…` : text);
const cap = text => text.charAt(0).toUpperCase() + text.slice(1);
const firstSentence = text => clip((String(text).match(/^.*?[.!?](?=\s|$)/)?.[0] || String(text)).trim(), 110);

export const money = n => (n == null ? '—' : `$${Math.round(n).toLocaleString('en-US')}`);
const compact = n => (n >= 1e6 ? `$${(n / 1e6).toFixed(2)}M` : `$${Math.round(n / 1e3)}K`);
const months = n => `${Number(n.toFixed(1))} month${n === 1 ? '' : 's'}`;

function requirementItems(r) {
  const items = [];
  if (r.sites?.length) items.push(`Sites: ${r.sites.join(', ')}`);
  if (r.bandwidth) items.push(`Bandwidth: ${r.bandwidth} per site`);
  if (r.sla) items.push(`Availability SLA: ${r.sla}`);
  if (r.clouds?.length) items.push(`Cloud connectivity: ${r.clouds.join(', ')}`);
  (r.software_components || []).forEach(c => items.push(`Software: ${c}`));
  if (r.integrations?.length) items.push(`Integrations: ${r.integrations.join(', ')}`);
  (r.security || []).forEach(s => items.push(`Security: ${s}`));
  if (r.timeline) items.push(`Target go-live: ${r.timeline}`);
  if (r.budget) items.push(`Budget: ${r.budget}`);
  return items.length ? items : [r.summary || 'No specific requirements were stated.'];
}

function timelineMetric(requirement, roadmap) {
  const fits = roadmap?.integrated?.fits_requested_timeline;
  const note = fits === false ? 'At risk: shorter than comparable projects or the plan'
    : fits === true ? 'Within the computed plan'
    : requirement.timeline ? 'Not confirmed' : 'No timeline stated';
  return { value: requirement.timeline || '—', note };
}

function networkView(net, requirement) {
  const designed = net?.status === 'designed';
  return {
    designed,
    summary: clean(net?.recommended_solution) || net?.provisioning?.reason || 'No network design yet.',
    reason: net?.provisioning?.reason,
    locations: net?.architecture?.sites || requirement.sites || [],
    clouds: net?.architecture?.cloud_connectivity || requirement.clouds || [],
    hub: net?.architecture?.cloud_hub ? clean(net.architecture.cloud_hub.name) : null,
    availability: net?.architecture?.availability_pct ?? null,
    leadTimeDays: net?.lead_time_days ?? null,
    components: (net?.bom || []).map(b => ({
      name: clean(b.item), qty: b.quantity, setup: b.unit_setup_cost, monthly: b.unit_monthly_cost,
      source: /^MCGW|Multi-Cloud/.test(clean(b.item)) ? 'MCGW rate card' : (tagOf(b.item) === 'mock' ? 'Mock catalog' : 'Catalog'),
    })),
    costSummary: net?.cost_summary || null,
    costRange: net?.cost_range || null,
    alternatives: net?.alternatives || [],
    assumptions: net?.assumptions || [],
    blockers: net?.provisioning?.blockers || [],
  };
}

function softwareView(sw) {
  if (!sw?.required) return { required: false, summary: sw?.recommended_solution || 'No custom software was requested.' };
  return {
    required: true,
    summary: clean(sw.recommended_solution),
    stack: sw.stack || [],
    architecture: sw.architecture || {},
    features: sw.features || [],
    integrations: sw.integrations || [],
    database: sw.database || { entities: [] },
    phases: (sw.phases || []).map(p => ({ name: p.name, weeks: p.duration_weeks, milestone: p.milestone, epics: p.epics })),
    deployment: sw.deployment || {},
    effort: sw.effort,
    assumptions: sw.assumptions || [],
  };
}

export function toProposal(state) {
  const p = state.proposal;
  const v = state.validation || {};
  const requirement = state.requirement || {};
  const costs = p.cost_summary || {};
  const total = costs.total_first_year;
  const confidence = v.confidence ?? 0;

  return {
    id: `QTP-${state.request_id.slice(0, 8).toUpperCase()}`,
    name: clean(p.title).replace(/^Proposal:\s*/i, '') || 'Untitled proposal',
    summary: p.executive_summary,
    keyPoints: p.summary_detail?.key_points || [],
    nextSteps: p.summary_detail?.next_steps || [],
    summarySource: p.summary_detail?.source,
    cost: total ? `${compact(total.minimum)}–${compact(total.maximum)}` : 'Not priced',
    costNote: total ? 'First-year range: list price plus planning contingency' : 'Needs sites and bandwidth first',
    risk: Math.round((1 - confidence) * 100),
    timeline: timelineMetric(requirement, p.roadmap),
    confidence: `${Math.round(confidence * 100)}%`,
    verdict: v.verdict,
    status: VERDICTS[v.verdict] || 'Assessed',
    needsReview: Boolean(v.needs_human_review),
    totalSeconds: state.timings?.total,
    timings: state.timings || {},
    requirements: requirementItems(requirement),
    assumptions: [...new Set((p.assumptions || []).map(clean))],
    openQuestions: p.open_questions || [],
    checks: (v.checks || []).map(c => ({ name: c.name.replace(/_/g, ' '), status: c.status, message: clean(c.message) })),
    risks: (p.risks || []).map(r => ({ level: cap(r.severity), title: firstSentence(clean(r.description)), note: r.mitigation, source: r.source })),
    network: networkView(state.network, requirement),
    software: softwareView(state.software),
    costs,
    roadmap: p.roadmap,
    similar: (p.similar_projects || []).map(s => ({
      name: clean(s.name), score: `${Math.round(s.similarity * 100)}%`, source: s.source,
      lesson: (s.lessons_learned || [])[0] || '', months: s.duration_months,
    })),
    provisioningJson: p.provisioning_json,
    provisioningReady: Boolean(p.provisioning_status?.ready),
    provisioningNote: p.provisioning_status?.message,
    commercialNote: p.commercial_status?.message,
    raw: state,
  };
}

export { months };
