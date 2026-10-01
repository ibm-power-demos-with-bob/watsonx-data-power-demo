/**
 * outcome-data.ts — static scenario data and Power pillar definitions for the Outcome page.
 * Extracted from outcome.tsx to keep the page file manageable.
 */

// ── Timeline bar data ─────────────────────────────────────────────────────────

export const CYBER_OLD = {
  label: 'Old world — Static report',
  color: '#da1e28',
  bgColor: '#fff1f1',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated', type: 'start' },
    { time: 'Fri–Sun',   event: 'Breach escalates undetected', type: 'bad' },
    { time: 'Mon 08:30', event: 'Supplier calls to say they can\'t fulfil', type: 'bad' },
    { time: 'Mon 11:00', event: 'Exposure confirmed: £47,230', type: 'bad' },
    { time: 'Mon 14:00', event: 'Alternative supplier found', type: 'bad' },
    { time: 'Tue–Wed',   event: '3 SLA breaches. £8,400 expediting costs.', type: 'cost' },
  ],
  actionAt: 4,
  cost: '£15,200',
  costLabel: 'SLA breaches + expediting + emergency premium',
  timeToAction: '~80 hours',
}

export const CYBER_NEW = {
  label: 'New world — watsonx.data federation',
  color: '#24a148',
  bgColor: '#defbe6',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated', type: 'start' },
    { time: 'Fri 11:14', event: 'Threat intelligence signal ingested to Iceberg', type: 'alert' },
    { time: 'Fri 11:14', event: 'Federated detection: IBM i \u00d7 EDB \u00d7 Threat Feed in under 2s', type: 'action' },
    { time: 'Fri 11:30', event: 'Alternative supplier pre-qualified', type: 'action' },
    { time: 'Fri 14:00', event: '11 of 14 POs re-routed. SLAs protected.', type: 'saved' },
  ],
  actionAt: 2,
  cost: '£1,200',
  costLabel: 'Rerouting admin only — SLA breaches: 0',
  timeToAction: '~5 hours',
}

export const WILDFIRE_OLD = {
  label: 'Old world — Static report',
  color: '#da1e28',
  bgColor: '#fff1f1',
  slots: [
    { time: 'Fri 06:00', event: 'Report generated — all routes clear', type: 'start' },
    { time: 'Mon 06:00', event: 'Wildfire closes A9/AP-7 corridor', type: 'bad' },
    { time: 'Mon–Wed',   event: '3 missed ship limits. No visibility.', type: 'bad' },
    { time: 'Wed 10:00', event: 'Rerouting finally arranged', type: 'bad' },
    { time: 'Thu',       event: '2 SLA breaches. £6,800 expediting.', type: 'cost' },
    { time: 'Fri+7',     event: 'Next report reflects last week\'s disruption', type: 'cost' },
  ],
  actionAt: 3,
  cost: '£8,700',
  costLabel: '2 SLA breaches + expediting + stock transfer',
  timeToAction: '~96 hours',
}

export const WILDFIRE_NEW = {
  label: 'New world — watsonx.data federation',
  color: '#24a148',
  bgColor: '#defbe6',
  slots: [
    { time: 'Mon 06:00', event: 'Route Disruption feed signals A9/AP-7 closure', type: 'alert' },
    { time: 'Mon 06:02', event: 'Signal ingested → federated detector runs in under 2s', type: 'action' },
    { time: 'Mon 06:15', event: 'On-call manager alerted, rerouting pre-approved', type: 'action' },
    { time: 'Mon 07:30', event: '5 of 7 POs rerouted before business day starts', type: 'saved' },
    { time: 'Mon EOD',   event: 'SLA breaches: 0. Stockouts: 0.', type: 'saved' },
  ],
  actionAt: 1,
  cost: '£1,900',
  costLabel: 'Rerouting admin only — SLA breaches: 0',
  timeToAction: '~90 minutes',
}

// ── Power Pillars ─────────────────────────────────────────────────────────────

export const PILLAR_IBMI = {
  icon: '⚙',
  colour: '#4589ff',
  title: 'Your ERP Runs on IBM Power — Federation Reaches It Directly',
  subtitle: 'Zero-ETL access to the system of record',
  points: [
    'Your core ERP (IBM i, Db2 for i) already runs on IBM Power — 99k+ orders, 32k products, live today.',
    'watsonx.data federates directly to Db2 for i via the native connector — no ETL, no data movement, no copy.',
    'The data your ERP has always owned becomes joinable with tier-2 supplier graphs and live threat feeds in seconds.',
    'This is not legacy modernisation — it\'s unlocking the asset you already have.',
  ],
}

export const PILLAR_MMA = {
  icon: '⚡',
  colour: '#08bdba',
  title: 'Real-Time Federation & On-Box AI — No GPU Cluster Required',
  subtitle: 'Sub-second cross-system joins with built-in Matrix Math Acceleration',
  points: [
    'Continuous detection queries run on RHEL on IBM Power — genuine Power hardware, not cloud abstraction.',
    'Federation links IBM i ERP, operational databases, and streaming signals in under 2 seconds — turning weekly reports into live operational response.',
    'Teams react in minutes (manual) or seconds (automated) before business operations are disrupted.',
    'IBM Power\'s Matrix Math Accelerator (MMA) enables on-box AI risk scoring and pattern matching — no separate GPU infrastructure, no data egress.',
  ],
}

export const PILLAR_CYBER = {
  icon: '🔒',
  colour: '#be95ff',
  title: 'Inherent Security Posture — Shrinks the Blast Radius',
  subtitle: 'Architecture-level resilience for supply chain attacks',
  points: [
    'IBM i\'s object-based memory architecture neutralises common exploit vectors — buffer overflows, code injection simply don\'t work.',
    'Running your ERP on IBM Power isn\'t just a performance choice — it\'s a security posture that limits blast radius of supply chain compromises like the one in this demo.',
    'PowerSC provides continuous security monitoring and compliance scoring for Power workloads — built-in, not bolted-on.',
    'Single vendor accountability: IBM owns the ERP, the hardware, the lakehouse, and the security layer.',
  ],
}

export const PILLAR_HYBRID = {
  icon: '☁',
  colour: '#be95ff',
  title: 'Hybrid Cloud Continuity — Workload Mobility Without Re-platforming',
  subtitle: 'On-prem resilience + cloud flexibility on the same ISA',
  points: [
    'IBM Power\'s hybrid cloud flexibility means your ERP and operational data span on-prem and IBM Cloud seamlessly.',
    'When a physical region is disrupted — road closure, wildfire, flooding — workloads move without re-platforming or data re-sync.',
    'The data your watsonx.data federation queries doesn\'t have to be at risk just because a logistics corridor is.',
    'Same ISA, same operating model, same security posture — wherever the workload needs to run.',
  ],
}

export const POWER_PILLARS: Record<'cyber' | 'wildfire', typeof PILLAR_IBMI[]> = {
  cyber:    [PILLAR_IBMI, PILLAR_MMA, PILLAR_CYBER],
  wildfire: [PILLAR_IBMI, PILLAR_MMA, PILLAR_HYBRID],
}
