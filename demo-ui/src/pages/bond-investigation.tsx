import Head from 'next/head'
import { useState } from 'react'
import { useRouter } from 'next/router'
import { HeaderName } from '@carbon/react'
import type { BondQueryResult } from './api/bond-query'
import { useAudience } from '../context/AudienceContext'

const ACTS = [
  { num: 1, label: 'Act 1: Naive Query', subtitle: 'The 1-D Question', desc: 'Queries raw career credits for post-Bond vs pre-Bond average ratings.' },
  { num: 2, label: 'Act 2: Relative Baseline', subtitle: 'Longevity & Volume', desc: 'Aggregates per-actress credit counts and active years, grouped by Bond era.' },
  { num: 3, label: 'Act 3: 3 Clocks Join', subtitle: 'Confounders Discovered', desc: 'Joins performer age at casting with decade-level average vote counts from a second table.' },
  { num: 4, label: 'Act 4: Character Depth', subtitle: 'Agency Matrix', desc: 'Correlates a 10-point character depth score, derived from James Bond Wiki text, with long-term post-Bond career trajectory.' },
  { num: 5, label: 'Act 5: Beyond Structured Columns', subtitle: 'Embedding Similarity (Static Demo)', desc: 'Ranks 231 linked excerpts (Bond Wiki character pages, Wikipedia, a few scholarly quotes) by cosine similarity using real, pre-computed embeddings. Live embedding and RAG are something we could add.' },
  { num: 6, label: 'Act 6: Lakehouse Synthesis', subtitle: 'The Smartphone Model', desc: 'Joins relational credits, decade benchmarks, and stored embedding similarity in one Presto query.' },
]

export default function BondInvestigationPage() {
  const router = useRouter()
  const { isSecurity, isTechnical, isExecutive, isOperations } = useAudience()

  const [activeAct, setActiveAct] = useState<number>(1)
  const [data, setData] = useState<BondQueryResult | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [hasExecuted, setHasExecuted] = useState<boolean>(false)
  const [showSql, setShowSql] = useState<boolean>(true)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  function handleSwitchAct(actNum: number) {
    setActiveAct(actNum)
    setData(null)
    setHasExecuted(false)
    setErrorMsg(null)
  }

  async function executeLiveQuery(actNum: number) {
    setLoading(true)
    setErrorMsg(null)
    try {
      const res = await fetch(`/api/bond-query?act=${actNum}`)
      if (res.ok) {
        const json: BondQueryResult = await res.json()
        setData(json)
        setHasExecuted(true)
      } else {
        const errJson = await res.json()
        setErrorMsg(errJson.error || 'Failed to execute query on Presto')
      }
    } catch (err: any) {
      console.error('Error fetching bond query:', err)
      setErrorMsg(err.message || 'Network error reaching Presto')
    } finally {
      setLoading(false)
    }
  }

  const currentActMeta = ACTS.find((a) => a.num === activeAct) || ACTS[0]

  return (
    <>
      <Head>
        <title>watsonx.data — Strategic Intelligence (The 60-Year Investigation)</title>
      </Head>

      <div style={{
        display: 'grid',
        gridTemplateRows: '48px 1fr',
        height: '100vh',
        background: 'var(--demo-bg)',
        color: 'var(--demo-text)',
        overflow: 'hidden',
        fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
      }}>
        {/* Top Header */}
        <header style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          borderBottom: '1px solid var(--demo-border)',
          background: 'var(--demo-surface)',
          gap: 16,
          flexShrink: 0,
        }}>
          <HeaderName prefix="IBM" href="/" style={{ paddingLeft: 0, textDecoration: 'none' }}>
            watsonx.data
          </HeaderName>
          <span style={{ fontSize: 12, color: 'var(--demo-text-muted)', borderLeft: '1px solid var(--demo-border)', paddingLeft: 12 }}>
            Strategic Intelligence ("Business Like a Smartphone")
          </span>
          <div style={{ flex: 1 }} />

          {/* Navigation Buttons */}
          <button onClick={() => router.push('/')}
            style={{ background: 'transparent', border: '1px solid var(--demo-border)', color: 'var(--demo-text-muted)', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            🗺️ Static Map
          </button>
          <button onClick={() => router.push('/live?scenario=cyber')}
            style={{ background: 'transparent', border: '1px solid var(--demo-border)', color: 'var(--demo-text-muted)', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            🧭 Live Satnav (OLIST)
          </button>
          <button onClick={() => router.push('/sources')}
            style={{ background: 'transparent', border: '1px solid var(--demo-border)', color: 'var(--demo-text-muted)', borderRadius: 2, padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
            🏗️ Architecture
          </button>
        </header>

        {/* Main Workspace Layout */}
        <div style={{
          display: 'grid',
          gridTemplateRows: 'auto 1fr',
          overflow: 'hidden',
          background: 'var(--demo-bg)',
        }}>
          {/* 6-Act Stepper Bar */}
          <div style={{
            background: 'var(--demo-surface)',
            borderBottom: '1px solid var(--demo-border)',
            padding: '12px 20px',
            display: 'flex',
            gap: 10,
            overflowX: 'auto',
          }}>
            {ACTS.map((act) => {
              const isActive = activeAct === act.num
              return (
                <button
                  key={act.num}
                  onClick={() => handleSwitchAct(act.num)}
                  style={{
                    flex: '1 1 0',
                    minWidth: 160,
                    padding: '10px 14px',
                    borderRadius: 4,
                    border: isActive ? '2px solid var(--demo-blue)' : '1px solid var(--demo-border)',
                    background: isActive ? 'var(--demo-surface-2)' : 'var(--demo-bg)',
                    color: isActive ? 'var(--demo-blue)' : 'var(--demo-text)',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 2 }}>
                    {act.label}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--demo-text-muted)' }}>
                    {act.subtitle}
                  </div>
                </button>
              )
            })}
          </div>

          {/* Body Content Area */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 380px',
            overflow: 'hidden',
            gap: 1,
            background: 'var(--demo-border)',
          }}>
            {/* Left: Query Execution & Visual Table */}
            <div style={{
              background: 'var(--demo-bg)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto',
              minHeight: 0,
              padding: 20,
            }}>
              {/* Act Header & Live Execution Trigger */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 16,
                flexShrink: 0,
              }}>
                <div>
                  <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--demo-text)' }}>
                    {data?.title || `${currentActMeta.label} — ${currentActMeta.subtitle}`}
                  </h2>
                  <p style={{ fontSize: 13, color: 'var(--demo-text-muted)', margin: '4px 0 0 0' }}>
                    {data?.subtitle || currentActMeta.desc}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    onClick={() => executeLiveQuery(activeAct)}
                    disabled={loading}
                    style={{
                      background: hasExecuted ? 'var(--demo-surface-2)' : 'var(--demo-blue)',
                      color: hasExecuted ? 'var(--demo-blue)' : '#fff',
                      border: hasExecuted ? '1px solid var(--demo-blue)' : 'none',
                      borderRadius: 4,
                      padding: '8px 18px',
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: loading ? 'wait' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      boxShadow: hasExecuted ? 'none' : '0 2px 6px rgba(15, 98, 254, 0.4)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <span>{loading ? '⚡ Running Presto query...' : hasExecuted ? '🔄 Re-Run Live Query' : '▶ Run watsonx.data Query'}</span>
                  </button>
                </div>
              </div>

              {/* Error Callout if query fails */}
              {errorMsg && (
                <div style={{
                  background: '#fff1f1',
                  border: '1px solid #da1e28',
                  borderRadius: 4,
                  padding: '12px 16px',
                  color: '#da1e28',
                  marginBottom: 16,
                  fontSize: 12,
                }}>
                  <strong>Query Error:</strong> {errorMsg}
                </div>
              )}

              {/* KPI Summary Tiles (Shown only after execution) */}
              {hasExecuted && data && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: 12,
                  marginBottom: 16,
                  flexShrink: 0,
                }}>
                  {Object.entries(data.summaryStats).map(([k, v]) => (
                    <div key={k} style={{
                      background: 'var(--demo-surface)',
                      border: '1px solid var(--demo-border)',
                      borderRadius: 4,
                      padding: '10px 14px',
                    }}>
                      <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {k}
                      </div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--demo-text)', marginTop: 4 }}>
                        {v}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Main Table / Unexecuted Placeholder */}
              <div style={{
                flex: 1,
                minHeight: 240,
                overflow: 'auto',
                border: '1px solid var(--demo-border)',
                borderRadius: 4,
                background: 'var(--demo-surface)',
                display: 'flex',
                flexDirection: 'column',
              }}>
                {!hasExecuted && !loading ? (
                  <div style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 40,
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 42, marginBottom: 16 }}>📊</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--demo-text)', marginBottom: 8 }}>
                      Query Ready for Live Presto Execution
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--demo-text-muted)', maxWidth: 480, lineHeight: 1.5, marginBottom: 20 }}>
                      Click <strong>"Run watsonx.data Query"</strong> to execute this statement live through the watsonx.data Presto engine.
                    </div>
                    <button
                      onClick={() => executeLiveQuery(activeAct)}
                      style={{
                        background: 'var(--demo-blue)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: 4,
                        padding: '10px 24px',
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      ▶ Run {currentActMeta.label}
                    </button>
                  </div>
                ) : loading ? (
                  <div style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 40,
                    textAlign: 'center',
                  }}>
                    <div style={{ fontSize: 32, marginBottom: 16, animation: 'spin 1.5s linear infinite' }}>⚡</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--demo-blue)', marginBottom: 6 }}>
                      Executing Query on watsonx.data Presto Engine...
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--demo-text-muted)' }}>
                      Querying data sources through watsonx.data
                    </div>
                  </div>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'var(--demo-surface-2)', borderBottom: '1px solid var(--demo-border)', position: 'sticky', top: 0, zIndex: 10 }}>
                        {data?.columns.map((col) => (
                          <th key={col.key} style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--demo-text)' }}>
                            {col.header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data?.rows.map((row, idx) => (
                        <tr key={idx} style={{
                          borderBottom: '1px solid var(--demo-border)',
                          background: idx % 2 === 0 ? 'var(--demo-surface)' : 'var(--demo-bg)',
                        }}>
                          {data.columns.map((col) => {
                            const val = row[col.key]
                            return (
                              <td key={col.key} style={{ padding: '8px 12px', color: 'var(--demo-text)' }}>
                                {col.format === 'score' ? (
                                  <span style={{
                                    fontWeight: 700,
                                    color: typeof val === 'number' && val > 0 ? 'var(--demo-green)' : typeof val === 'number' && val < 0 ? 'var(--demo-red)' : 'var(--demo-text)',
                                  }}>
                                    {typeof val === 'number' ? val.toFixed(2) : val}
                                  </span>
                                ) : col.format === 'link' ? (
                                  typeof val === 'string' && /^https:\/\//.test(val) ? (
                                    <a href={val} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--demo-accent, #78a9ff)', fontSize: 11 }}>
                                      Source ↗
                                    </a>
                                  ) : (
                                    '—'
                                  )
                                ) : col.format === 'tag' ? (
                                  <span style={{
                                    background: 'var(--demo-surface-2)',
                                    border: '1px solid var(--demo-border)',
                                    borderRadius: 10,
                                    padding: '2px 8px',
                                    fontSize: 10,
                                    fontWeight: 600,
                                  }}>
                                    {val}
                                  </span>
                                ) : (
                                  val
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Methodological Context & Scholarship Notes */}
              {hasExecuted && data?.notes && Object.keys(data.notes).length > 0 && (
                <div style={{
                  marginTop: 16,
                  background: 'var(--demo-surface)',
                  border: '1px solid var(--demo-border)',
                  borderRadius: 4,
                  padding: '14px 16px',
                  flexShrink: 0,
                }}>
                  <div style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: 'var(--demo-blue)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 10,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}>
                    <span>📚</span> Methodological Context & Scholarship
                  </div>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: 12,
                  }}>
                    {Object.entries(data.notes).map(([title, content]) => (
                      <div key={title} style={{
                        background: 'var(--demo-bg)',
                        border: '1px solid var(--demo-border)',
                        borderRadius: 4,
                        padding: '10px 14px',
                      }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--demo-text)', marginBottom: 4 }}>
                          {title}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', lineHeight: 1.5 }}>
                          {content}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Technical Query Details & Business Bridge */}
            <div style={{
              background: 'var(--demo-surface)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto',
              padding: 20,
              gap: 16,
            }}>
              {/* Catalogs Queried & Latency */}
              <div style={{
                background: 'var(--demo-bg)',
                border: '1px solid var(--demo-border)',
                borderRadius: 4,
                padding: 14,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--demo-blue)', letterSpacing: '0.05em' }}>
                    Lakehouse Engine & Catalogs
                  </span>
                  {hasExecuted && (
                    <span style={{ fontSize: 11, color: 'var(--demo-green)', fontWeight: 600 }}>
                      ⚡ {data?.executionTimeMs} ms
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {(data?.catalogsQueried || [
                    { name: 'bond_career_analysis', engine: 'Relational table', role: 'Performer bio & credits' }
                  ]).map((cat) => (
                    <div key={cat.name} style={{
                      background: 'var(--demo-surface)',
                      border: '1px solid var(--demo-border)',
                      borderRadius: 3,
                      padding: '6px 10px',
                      fontSize: 11,
                    }}>
                      <div style={{ fontWeight: 600, color: 'var(--demo-text)' }}>
                        {cat.name} <span style={{ fontWeight: 400, color: 'var(--demo-text-muted)' }}>({cat.engine})</span>
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--demo-text-muted)', marginTop: 2 }}>
                        {cat.role}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SQL Query Plan */}
              <div style={{
                background: 'var(--demo-bg)',
                border: '1px solid var(--demo-border)',
                borderRadius: 4,
                padding: 14,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--demo-text-muted)', letterSpacing: '0.05em' }}>
                    watsonx.data Query Text
                  </span>
                  <button
                    onClick={() => setShowSql(!showSql)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--demo-blue)', fontSize: 11, cursor: 'pointer' }}
                  >
                    {showSql ? 'Hide SQL' : 'Show SQL'}
                  </button>
                </div>
                {showSql && (
                  <pre style={{
                    margin: 0,
                    padding: 10,
                    background: '#12161a',
                    color: '#e0e0e0',
                    borderRadius: 3,
                    fontSize: 10,
                    lineHeight: 1.4,
                    overflowX: 'auto',
                    fontFamily: "'IBM Plex Mono', monospace",
                  }}>
                    {data?.sql || `-- Select Act to view query plan`}
                  </pre>
                )}
              </div>

              {/* Data provenance: what is real, derived or editorial, and where each piece runs */}
              <div style={{
                background: 'var(--demo-bg)',
                border: '1px solid var(--demo-border)',
                borderRadius: 4,
                padding: 14,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: 'var(--demo-text-muted)', letterSpacing: '0.05em', marginBottom: 8 }}>
                  About this demo's data
                </div>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11, lineHeight: 1.5, color: 'var(--demo-text-muted)' }}>
                  <li><strong>Credits, ratings, votes, decade averages:</strong> derived from the public IMDb datasets (non-commercial use).</li>
                  <li><strong>Cast list:</strong> 88 film roles: an initial curated list of 43, plus 45 added from the Fandom "Bond Girl Actresses" category. Most names also appear on MI6-HQ. It is a sample to show data coming together, not an exhaustive list.</li>
                  <li><strong>Character attributes (agency score, survives the film, takes part in the climax, independent objective, expertise, combat or intelligence role):</strong> not in IMDb. Derived from the Biography and Personality text of each character's James Bond Wiki (Fandom, CC BY-SA) page with a simple keyword rubric; the supporting sentence for each flag and the earlier hand-typed score are stored beside it. Rows with a short or missing page are marked low-confidence or editorial-only. Role category and occupation are still hand-typed. This is unstructured text turned into structured columns and joined to the IMDb-derived ones; the rubric is crude and some scores will look wrong to a Bond fan.</li>
                  <li><strong>Text excerpts:</strong> James Bond Wiki character pages (CC BY-SA, linked to the exact revision), English Wikipedia actress articles (CC BY-SA 4.0, linked to the exact revision), plus 7 short attributed quotes from Lisa Funnell, "Nomi/No Me?" (Flow, 2019). The Act 4 scholarship note cites the Flow article and the Participations survey paper (both read in full) and published abstracts for the rest.</li>
                  <li><strong>Where it runs:</strong> the PostgreSQL (RHEL) and Db2 for i sources run on IBM Power. The watsonx.data Presto engine in this demo runs on x86 (VMware); watsonx.data is supported on IBM Power.</li>
                </ul>
              </div>

              {/* The Commercial Bridge to Business on Monday */}
              <div style={{
                background: 'var(--demo-surface-2)',
                border: '1px solid var(--demo-border)',
                borderRadius: 4,
                padding: 16,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
                  <span style={{ fontSize: 16 }}>💼</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--demo-text)' }}>
                    Commercial Bridge: From Bond to Your Business
                  </span>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--demo-blue)', textTransform: 'uppercase', marginBottom: 2 }}>
                    What We Learned in Bond
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--demo-text)', lineHeight: 1.5 }}>
                    {data?.businessInsight.bondTakeaway || 'Run query to view longitudinal insight.'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--demo-green)', textTransform: 'uppercase', marginBottom: 2 }}>
                    Your Enterprise Reality on Monday
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--demo-text-muted)', lineHeight: 1.5 }}>
                    {data?.businessInsight.enterpriseTranslation || 'Run query to view enterprise translation.'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// Made with Bob
