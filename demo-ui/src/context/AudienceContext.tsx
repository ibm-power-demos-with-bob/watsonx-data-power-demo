'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

export type Audience = 'ciso' | 'architect' | 'supply-chain' | 'exec' | 'balanced'

interface AudienceContextValue {
  audience: Audience
  setAudience: (a: Audience) => void
  isTechnical: boolean
  isExecutive: boolean
  isSecurity: boolean
  isOperations: boolean
}

const AudienceContext = createContext<AudienceContextValue | null>(null)

const AUDIENCE_LABELS: Record<Audience, string> = {
  ciso: 'CISO / Security',
  architect: 'Data Architect',
  'supply-chain': 'Supply-Chain / Procurement',
  exec: 'IT Director / C-Suite',
  balanced: 'Balanced (Default)',
}

const AUDIENCE_FLAGS: Record<Audience, { isTechnical: boolean; isExecutive: boolean; isSecurity: boolean; isOperations: boolean }> = {
  ciso:       { isTechnical: true,  isExecutive: false, isSecurity: true,  isOperations: false },
  architect:  { isTechnical: true,  isExecutive: false, isSecurity: false, isOperations: false },
  'supply-chain': { isTechnical: false, isExecutive: false, isSecurity: false, isOperations: true  },
  exec:       { isTechnical: false, isExecutive: true,  isSecurity: false, isOperations: true  },
  balanced:   { isTechnical: true,  isExecutive: true,  isSecurity: true,  isOperations: true  },
}

export function AudienceProvider({ children }: { children: ReactNode }) {
  const [audience, setAudienceState] = useState<Audience>('balanced')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // 1. Check query param first (highest priority for demo links)
    const params = new URLSearchParams(window.location.search)
    const paramAudience = params.get('audience') as Audience | null
    if (paramAudience && paramAudience in AUDIENCE_LABELS) {
      setAudienceState(paramAudience)
      return
    }
    // 2. Check localStorage (persists during demo session)
    const stored = localStorage.getItem('demo-audience') as Audience | null
    if (stored && stored in AUDIENCE_LABELS) {
      setAudienceState(stored)
      return
    }
    // 3. Check env var (build-time default) — would be injected via NEXT_PUBLIC_DEMO_AUDIENCE
    // Note: In Next.js, env vars are embedded at build time, so this is a fallback
  }, [])

  const setAudience = (a: Audience) => {
    setAudienceState(a)
    localStorage.setItem('demo-audience', a)
  }

  const flags = AUDIENCE_FLAGS[audience]

  if (!mounted) {
    return <>{children}</>
  }

  return (
    <AudienceContext.Provider value={{ audience, setAudience, ...flags }}>
      {children}
    </AudienceContext.Provider>
  )
}

export function useAudience() {
  const ctx = useContext(AudienceContext)
  if (!ctx) {
    // Return balanced defaults if not wrapped in provider
    return {
      audience: 'balanced' as Audience,
      setAudience: () => {},
      isTechnical: true,
      isExecutive: true,
      isSecurity: true,
      isOperations: true,
    }
  }
  return ctx
}

export function useAudienceLabel() {
  const { audience } = useAudience()
  return AUDIENCE_LABELS[audience]
}

export function AudienceSelector() {
  const { audience, setAudience } = useAudience()

  return (
    <details style={{
      position: 'fixed',
      bottom: 16,
      right: 16,
      zIndex: 999,
      background: 'var(--demo-surface)',
      border: '1px solid var(--demo-border)',
      borderRadius: 4,
      padding: '8px',
      fontSize: 11,
      fontFamily: "'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif",
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    }}>
      <summary style={{
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '4px 8px',
        fontWeight: 600,
        color: 'var(--demo-text)',
      }}>
        <span style={{ color: 'var(--demo-blue)' }}>👥</span>
        <span>Audience: <strong>{AUDIENCE_LABELS[audience]}</strong></span>
      </summary>
      <div style={{ padding: '8px', display: 'flex', flexDirection: 'column', gap: 4, minWidth: 200 }}>
        {(Object.keys(AUDIENCE_LABELS) as Audience[]).map((a) => (
          <label key={a} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="radio"
              name="demo-audience"
              checked={audience === a}
              onChange={() => setAudience(a)}
              style={{ accentColor: 'var(--demo-blue)' }}
            />
            <span style={{ color: 'var(--demo-text)', fontSize: 12 }}>{AUDIENCE_LABELS[a]}</span>
            {a !== 'balanced' && (
              <span style={{
                marginLeft: 'auto',
                fontSize: 9,
                color: 'var(--demo-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}>
                {AUDIENCE_FLAGS[a].isTechnical && '🔧 '}
                {AUDIENCE_FLAGS[a].isSecurity && '🔒 '}
                {AUDIENCE_FLAGS[a].isOperations && '📦 '}
                {AUDIENCE_FLAGS[a].isExecutive && '🎯 '}
              </span>
            )}
          </label>
        ))}
      </div>
    </details>
  )
}