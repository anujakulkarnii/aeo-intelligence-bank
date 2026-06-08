import { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import {
  LayoutDashboard, MessageSquare, Zap, Lightbulb, Search,
  TrendingUp, FileText, Brain, Building2, Menu, X, ChevronRight,
  Sparkles, Loader2
} from 'lucide-react'

// ─── data ─────────────────────────────────────────────────────────────────

function useData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  useEffect(() => {
    fetch('/api/data').then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])
  return { data, loading, error }
}

// ─── helpers ─────────────────────────────────────────────────────────────

function fmtDate(d) {
  if (!d) return null
  try { return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) }
  catch { return d }
}

function bucketOf(source) {
  if (!source) return 'other'
  const s = source.toLowerCase()
  if (s.includes('reddit')) return 'Reddit'
  if (s.includes('g2') || s.includes('capterra') || s.includes('review')) return 'Review site'
  if (s.includes('transcript') || s.includes('call')) return 'Sales call'
  return 'Search'
}

const ALL_TEAMS = ['Sales', 'Product', 'Social', 'CS', 'Leadership']

// ─── global search ────────────────────────────────────────────────────────

const SECTION_LABELS = {
  icp_phrases: 'ICP Phrase',
  outbound_hooks: 'Hook',
  competitor_complaints: 'Competitor',
  hypotheses: 'Hypothesis',
  fanout_terms: 'Fanout',
  next_queries: 'Query',
  sales_calls: 'Sales Call',
  ai_citations: 'Citation',
}

const SECTION_NAV = {
  icp_phrases: 'icp',
  outbound_hooks: 'hooks',
  competitor_complaints: 'competitors',
  hypotheses: 'hypotheses',
  fanout_terms: 'fanout',
  next_queries: 'queries',
  sales_calls: 'transcripts',
  ai_citations: 'citations',
}

function getItemText(item, section) {
  return [
    item.text, item.hypothesis, item.term, item.query, item.complaint,
    item.tool, item.competitor, item.name, item.prospect, item.signal,
    item.action, ...(item.key_phrases || []), ...(item.teams || [])
  ].filter(Boolean).join(' ')
}

function searchAll(data, query) {
  if (!data || !query.trim()) return []
  const q = query.toLowerCase()
  const results = []
  Object.entries(SECTION_LABELS).forEach(([section, label]) => {
    const items = data[section] || []
    items.forEach(item => {
      const text = getItemText(item, section)
      if (text.toLowerCase().includes(q)) {
        const display = item.text || item.hypothesis || item.term || item.query ||
          item.complaint || item.tool || item.prospect || '—'
        results.push({ section, label, display, item })
      }
    })
  })
  return results.slice(0, 12)
}

function GlobalSearch({ data, onNavigate }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [aiAnswer, setAiAnswer] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const inputRef = useRef(null)
  const results = useMemo(() => searchAll(data, query), [data, query])

  useEffect(() => {
    function onKey(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        setOpen(true)
      }
      if (e.key === 'Escape') { setOpen(false); setQuery(''); setAiAnswer(null) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  function handleSelect(result) {
    onNavigate(SECTION_NAV[result.section])
    setOpen(false)
    setQuery('')
    setAiAnswer(null)
  }

  async function askAI() {
    if (!query.trim() || aiLoading) return
    setAiLoading(true)
    setAiAnswer(null)
    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query }),
      })
      const json = await res.json()
      setAiAnswer(json.answer || json.error || 'No answer returned.')
    } catch (e) {
      setAiAnswer('Error reaching the AI endpoint.')
    } finally {
      setAiLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') askAI()
  }

  function handleChange(e) {
    setQuery(e.target.value)
    setAiAnswer(null)
    setOpen(true)
  }

  return (
    <div className="relative w-full max-w-2xl">
      <div className={`flex items-center gap-2 h-9 px-3 rounded-lg border transition-all ${
        open ? 'border-foreground/20 bg-white shadow-sm' : 'border-border bg-muted/60 hover:bg-muted'
      }`}>
        <Search size={13} className="text-muted-foreground shrink-0" />
        <input
          ref={inputRef}
          value={query}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => { setOpen(false) }, 200)}
          placeholder="Search or ask anything… (↵ for AI answer)"
          className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
        />
        {query ? (
          <div className="flex items-center gap-1.5">
            {aiLoading
              ? <Loader2 size={12} className="text-muted-foreground animate-spin" />
              : (
                <button
                  onMouseDown={e => { e.preventDefault(); askAI() }}
                  className="flex items-center gap-1 text-2xs text-primary font-medium hover:underline"
                >
                  <Sparkles size={10} />Ask AI
                </button>
              )
            }
            <button onMouseDown={() => { setQuery(''); setAiAnswer(null); setOpen(false) }}>
              <X size={12} className="text-muted-foreground hover:text-foreground" />
            </button>
          </div>
        ) : (
          <kbd className="hidden sm:inline-flex items-center text-2xs text-muted-foreground border border-border rounded px-1 py-0.5 font-mono">⌘K</kbd>
        )}
      </div>

      {open && query.trim() && (
        <div className="absolute top-full mt-1.5 left-0 right-0 bg-white rounded-lg border border-border shadow-lg z-50 overflow-hidden max-h-[480px] overflow-y-auto">

          {/* AI Answer */}
          {(aiAnswer || aiLoading) && (
            <div className="p-4 border-b border-border bg-[#f0faf6]" style={{ borderLeft: '3px solid #1D9E75' }}>
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles size={11} className="text-primary" />
                <span className="text-2xs font-semibold text-primary uppercase tracking-wider">AI Answer</span>
              </div>
              {aiLoading
                ? <p className="text-sm text-muted-foreground animate-pulse">Thinking…</p>
                : <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{aiAnswer}</p>
              }
            </div>
          )}

          {/* Keyword results */}
          {!aiAnswer && results.length > 0 && (
            <div>
              {results.map((r, i) => (
                <button
                  key={i}
                  onMouseDown={() => handleSelect(r)}
                  className="w-full flex items-start gap-3 px-4 py-2.5 text-left transition-colors hover:bg-muted/60"
                >
                  <span className="shrink-0 text-2xs font-medium text-muted-foreground uppercase tracking-wider w-16 pt-0.5">{r.label}</span>
                  <span className="text-sm text-foreground leading-snug line-clamp-2 flex-1">{r.display}</span>
                  <ChevronRight size={12} className="text-muted-foreground shrink-0 mt-1" />
                </button>
              ))}
              <div className="px-4 py-2 border-t border-border flex items-center justify-between">
                <span className="text-2xs text-muted-foreground">{results.length} results</span>
                <button
                  onMouseDown={e => { e.preventDefault(); askAI() }}
                  className="text-2xs text-primary font-medium flex items-center gap-1 hover:underline"
                >
                  <Sparkles size={10} />Ask AI instead
                </button>
              </div>
            </div>
          )}

          {!aiAnswer && results.length === 0 && !aiLoading && (
            <div className="px-4 py-4">
              <p className="text-sm text-muted-foreground mb-2">No keyword matches for "{query}"</p>
              <button
                onMouseDown={e => { e.preventDefault(); askAI() }}
                className="flex items-center gap-1.5 text-sm text-primary font-medium hover:underline"
              >
                <Sparkles size={12} />Ask AI about this
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── sidebar ──────────────────────────────────────────────────────────────

const NAV = [
  { id: 'overview',    label: 'Overview',      icon: LayoutDashboard },
  { id: 'icp',         label: 'ICP Phrases',   icon: MessageSquare },
  { id: 'hooks',       label: 'Hooks',         icon: Zap },
  { id: 'competitors', label: 'Competitors',   icon: Building2 },
  { id: 'citations',   label: 'AI Citations',  icon: Brain },
  { id: 'hypotheses',  label: 'Hypotheses',    icon: Lightbulb },
  { id: 'fanout',      label: 'Fanout Terms',  icon: TrendingUp },
  { id: 'queries',     label: 'Next Queries',  icon: Search },
  { id: 'transcripts', label: 'Sales Calls',   icon: FileText },
]

function Sidebar({ active, setActive, open, setOpen, data }) {
  const counts = useMemo(() => {
    if (!data) return {}
    return {
      icp: data.icp_phrases?.length,
      hooks: data.outbound_hooks?.length,
      competitors: data.competitor_complaints?.length,
      citations: data.ai_citations?.length,
      hypotheses: data.hypotheses?.length,
      fanout: data.fanout_terms?.length,
      queries: data.next_queries?.length,
      transcripts: data.sales_calls?.length,
    }
  }, [data])

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/20 z-20 lg:hidden" onClick={() => setOpen(false)} />}
      <aside className={`
        fixed top-0 left-0 h-full z-30 flex flex-col w-[200px]
        bg-white border-r border-border
        transition-transform duration-200
        ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* Logo */}
        <div className="px-4 h-[52px] flex items-center border-b border-border">
          <div>
            <div className="text-base font-bold tracking-tight text-foreground">FrontlineHQ</div>
            <div className="text-2xs text-muted-foreground tracking-widest uppercase mt-0.5">AEO / GEO Bank</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-2 px-2">
          {NAV.map(item => {
            const Icon = item.icon
            const isActive = active === item.id
            const count = counts[item.id]
            return (
              <button
                key={item.id}
                onClick={() => { setActive(item.id); setOpen(false) }}
                className={`
                  w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-sm mb-0.5
                  transition-colors text-left group
                  ${isActive
                    ? 'bg-foreground text-background'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }
                `}
              >
                <Icon size={14} className="shrink-0" />
                <span className="flex-1 font-medium">{item.label}</span>
                {count > 0 && (
                  <span className={`text-2xs tabular-nums ${isActive ? 'text-background/60' : 'text-muted-foreground'}`}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {/* Footer */}
        {data?.meta && (
          <div className="px-4 py-3 border-t border-border">
            <p className="text-2xs text-muted-foreground">Run {data.meta.run_count} · {fmtDate(data.meta.last_run)}</p>
          </div>
        )}
      </aside>
    </>
  )
}

// ─── top bar ──────────────────────────────────────────────────────────────

function TopBar({ title, data, onNavigate, teamFilter, setTeamFilter, showTeamFilter, onMenuClick }) {
  return (
    <div className="sticky top-0 z-10 bg-background/90 backdrop-blur-md border-b border-border">
      {/* Search row */}
      <div className="h-[52px] flex items-center px-5 gap-3">
        <button onClick={onMenuClick} className="lg:hidden">
          <Menu size={16} className="text-muted-foreground" />
        </button>
        <div className="flex-1">
          <GlobalSearch data={data} onNavigate={onNavigate} />
        </div>
        {showTeamFilter && (
          <div className="hidden lg:flex items-center gap-1">
            {['All', ...ALL_TEAMS].map(t => (
              <button
                key={t}
                onClick={() => setTeamFilter(t === 'All' ? null : t)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  (t === 'All' && !teamFilter) || teamFilter === t
                    ? 'bg-foreground text-background'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </div>
      {/* Page title row */}
      <div className="px-6 py-2.5 border-t border-border">
        <h1 className="text-sm font-semibold text-foreground">{title}</h1>
      </div>
    </div>
  )
}

// ─── primitives ───────────────────────────────────────────────────────────

function Tag({ children, variant = 'default' }) {
  const styles = {
    default: 'bg-muted text-muted-foreground',
    green:   'bg-emerald-50 text-emerald-700',
    red:     'bg-red-50 text-red-500',
    amber:   'bg-amber-50 text-amber-700',
    strong:  'bg-foreground/5 text-foreground',
  }
  return (
    <span className={`inline-flex items-center rounded text-2xs font-medium px-1.5 py-0.5 ${styles[variant]}`}>
      {children}
    </span>
  )
}

function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-lg border border-border ${className}`}>
      {children}
    </div>
  )
}

function SectionHeader({ title, count, description }) {
  return (
    <div className="px-5 py-4 border-b border-border">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {count != null && <span className="text-xs text-muted-foreground">{count}</span>}
      </div>
      {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
    </div>
  )
}

// ─── stat card ────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-lg border p-4 ${highlight ? 'border-primary/20 bg-primary/[0.03]' : 'border-border bg-white'}`}>
      <p className="text-2xs text-muted-foreground uppercase tracking-widest mb-2">{label}</p>
      <p className={`text-4xl font-semibold tabular-nums leading-none tracking-tight ${highlight ? 'text-primary' : 'text-foreground'}`} style={{letterSpacing: '-0.04em'}}>
        {value}
      </p>
      {sub && <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">{sub}</p>}
    </div>
  )
}

// ─── bar chart ────────────────────────────────────────────────────────────

function BarChart({ data, valueKey = 'count', labelKey = 'name' }) {
  const max = Math.max(...data.map(d => d[valueKey] || 0), 1)
  return (
    <div className="space-y-2.5">
      {data.map((row, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="w-32 text-xs text-muted-foreground truncate shrink-0">{row[labelKey]}</span>
          <div className="flex-1 bg-muted rounded-full h-1 overflow-hidden">
            <div
              className="h-full bg-foreground/70 rounded-full"
              style={{ width: `${Math.round((row[valueKey] / max) * 100)}%`, transition: 'width 0.6s ease' }}
            />
          </div>
          <span className="text-xs tabular-nums text-muted-foreground w-5 text-right">{row[valueKey]}</span>
        </div>
      ))}
    </div>
  )
}

// ─── icp source card ─────────────────────────────────────────────────────

function IcpSourceCard({ sourceCounts, phrases }) {
  const [expanded, setExpanded] = useState(null)
  const max = Math.max(...sourceCounts.map(d => d.count), 1)

  const phrasesBySource = useMemo(() => {
    const map = {}
    phrases.forEach(p => {
      const b = bucketOf(p.source)
      if (!map[b]) map[b] = []
      map[b].push(p)
    })
    return map
  }, [phrases])

  return (
    <Card>
      <SectionHeader
        title="ICP Source Breakdown"
        description="Where your customers' exact language was found — click a source to see the phrases"
      />
      <div className="divide-y divide-border">
        {sourceCounts.map(row => {
          const isOpen = expanded === row.name
          const sourcePhrases = phrasesBySource[row.name] || []
          return (
            <div key={row.name}>
              <button
                onClick={() => setExpanded(isOpen ? null : row.name)}
                className="w-full flex items-center gap-3 px-6 py-3 hover:bg-muted/40 transition-colors text-left"
              >
                <span className="w-20 text-xs text-muted-foreground shrink-0">{row.name}</span>
                <div className="flex-1 bg-muted rounded-full h-1 overflow-hidden">
                  <div
                    className="h-full bg-foreground/70 rounded-full"
                    style={{ width: `${Math.round((row.count / max) * 100)}%`, transition: 'width 0.5s ease' }}
                  />
                </div>
                <span className="text-xs tabular-nums text-muted-foreground w-5 text-right">{row.count}</span>
                <ChevronRight size={12} className={`text-muted-foreground ml-1 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
              </button>
              {isOpen && (
                <div className="bg-muted/30 border-t border-border divide-y divide-border/60">
                  <div className="px-6 py-2">
                    <p className="text-2xs text-muted-foreground uppercase tracking-widest">
                      {row.count} phrase{row.count !== 1 ? 's' : ''} from {row.name} — exact language used by your market
                    </p>
                  </div>
                  {sourcePhrases.map(p => (
                    <div key={p.id} className="px-6 py-2.5 flex items-start gap-3">
                      <p className="text-sm text-foreground flex-1">"{p.text}"</p>
                      <div className="flex gap-1 shrink-0">
                        {(p.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

// ─── overview ────────────────────────────────────────────────────────────

function OverviewPage({ data }) {
  const citationRate = useMemo(() => {
    const items = data?.ai_citations || []
    if (!items.length) return null
    return Math.round((items.filter(c => c.frontlinehq_appears === true).length / items.length) * 100)
  }, [data])

  const stats = useMemo(() => {
    if (!data) return []
    const cited = data.ai_citations?.filter(c => c.frontlinehq_appears === true).length || 0
    const total = data.ai_citations?.length || 0
    return [
      { label: 'Citation Rate', value: citationRate != null ? `${citationRate}%` : '—',
        sub: total ? `${cited} of ${total} AI queries` : 'No AI checks yet', highlight: true },
      { label: 'ICP Phrases',    value: data.icp_phrases?.length || 0 },
      { label: 'Hooks',          value: data.outbound_hooks?.length || 0 },
      { label: 'Hypotheses',     value: data.hypotheses?.length || 0 },
      { label: 'Fanout Terms',   value: data.fanout_terms?.length || 0 },
      { label: 'Sales Calls',    value: data.sales_calls?.length || 0 },
    ]
  }, [data, citationRate])

  const competitorCounts = useMemo(() => {
    if (!data) return []
    const counts = {}
    ;(data.competitor_complaints || []).forEach(c => {
      const n = c.tool || c.competitor || c.name
      if (n) counts[n] = (counts[n] || 0) + 1
    })
    ;(data.citations || []).forEach(c =>
      (c.competitors_cited || []).forEach(n => { counts[n] = (counts[n] || 0) + 1 })
    )
    ;(data.ai_citations || []).forEach(c =>
      (c.competitors_cited || []).forEach(n => { counts[n] = (counts[n] || 0) + 1 })
    )
    return Object.entries(counts).map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count).slice(0, 8)
  }, [data])

  const sourceCounts = useMemo(() => {
    if (!data) return []
    const counts = {}
    ;(data.icp_phrases || []).forEach(p => {
      const b = bucketOf(p.source)
      counts[b] = (counts[b] || 0) + 1
    })
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)
  }, [data])

  const citationRows = useMemo(() => {
    if (!data?.ai_citations?.length) return []
    const byQuery = {}
    data.ai_citations.forEach(c => {
      if (!byQuery[c.query]) byQuery[c.query] = {}
      byQuery[c.query][c.model] = c.frontlinehq_appears === true
    })
    return Object.entries(byQuery).slice(0, 8).map(([query, models]) => ({ query, models }))
  }, [data])

  if (!data) return null

  return (
    <div className="p-6 space-y-5">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map(s => <StatCard key={s.label} {...s} />)}
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-4">
        {competitorCounts.length > 0 && (
          <Card>
            <SectionHeader title="Competitor Landscape" description="Mentions across all data sources" />
            <div className="p-6"><BarChart data={competitorCounts} /></div>
          </Card>
        )}
        {sourceCounts.length > 0 && (
          <IcpSourceCard sourceCounts={sourceCounts} phrases={data.icp_phrases || []} />
        )}
      </div>

      {/* Citation grid */}
      {citationRows.length > 0 && (
        <Card>
          <SectionHeader title="AI Engine Citation Grid" description="Does FrontlineHQ appear in AI engine responses?" />
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-5 py-2.5 text-2xs font-medium text-muted-foreground uppercase tracking-wider">Query</th>
                  {['perplexity', 'claude'].map(m => (
                    <th key={m} className="px-4 py-2.5 text-2xs font-medium text-muted-foreground uppercase tracking-wider capitalize text-center">{m}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {citationRows.map((row, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0">
                    <td className="px-5 py-3 text-xs text-muted-foreground max-w-xs truncate">{row.query}</td>
                    {['perplexity', 'claude'].map(m => (
                      <td key={m} className="px-4 py-3 text-center">
                        {row.models[m] === undefined
                          ? <span className="text-muted-foreground text-xs">—</span>
                          : row.models[m]
                            ? <span className="text-emerald-600 font-semibold text-sm">✓</span>
                            : <span className="text-red-400 font-semibold text-sm">✗</span>
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ICP phrases */}
      {data.icp_phrases?.length > 0 && (
        <Card>
          <SectionHeader title="Top ICP Phrases" description="Highest-signal language from customers" count={`${data.icp_phrases.length} total`} />
          <div className="divide-y divide-border">
            {data.icp_phrases.slice(0, 6).map(p => (
              <div key={p.id} className="px-5 py-3 flex items-start gap-4">
                <span className="text-2xs text-muted-foreground uppercase tracking-wider w-12 pt-0.5 shrink-0">{p.source}</span>
                <p className="text-sm text-foreground flex-1">"{p.text}"</p>
                <div className="flex gap-1 shrink-0">
                  {(p.teams || []).slice(0, 2).map(t => <Tag key={t}>{t}</Tag>)}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Hypotheses */}
      {data.hypotheses?.length > 0 && (
        <Card>
          <SectionHeader title="Latest Hypotheses" count={`${data.hypotheses.length} total`} />
          <div className="divide-y divide-border">
            {data.hypotheses.slice(0, 3).map(h => (
              <div key={h.id} className="px-5 py-4">
                <p className="text-sm text-foreground leading-relaxed">{h.hypothesis}</p>
                <div className="flex items-center gap-1.5 mt-2">
                  {(h.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
                  {h.strength === 'strong' && <Tag variant="green">strong</Tag>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// ─── icp page ────────────────────────────────────────────────────────────

function IcpPage({ data, search, teamFilter }) {
  const phrases = useMemo(() => {
    let items = data?.icp_phrases || []
    if (teamFilter) items = items.filter(p => p.teams?.includes(teamFilter))
    if (search) items = items.filter(p => p.text?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search, teamFilter])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="ICP Phrases" count={phrases.length} description="Customer language from community & reviews" />
        <div className="divide-y divide-border">
          {phrases.map(p => (
            <div key={p.id} className="px-5 py-3 flex items-start gap-4">
              <span className="text-2xs text-muted-foreground uppercase tracking-wider w-14 pt-0.5 shrink-0">{bucketOf(p.source)}</span>
              <p className="text-sm text-foreground flex-1">"{p.text}"</p>
              <div className="flex items-center gap-1.5 shrink-0">
                {(p.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
                {p.hot && <Tag variant="green">Hot</Tag>}
                {p.geography && p.geography !== 'Unknown' && <Tag>{p.geography}</Tag>}
              </div>
            </div>
          ))}
          {phrases.length === 0 && <EmptyState />}
        </div>
      </Card>
    </div>
  )
}

// ─── hooks page ──────────────────────────────────────────────────────────

function HooksPage({ data, search, teamFilter }) {
  const hooks = useMemo(() => {
    let items = data?.outbound_hooks || []
    if (teamFilter) items = items.filter(h => h.teams?.includes(teamFilter))
    if (search) items = items.filter(h => h.text?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search, teamFilter])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="Outbound Hooks" count={hooks.length} description="Message angles for sales & marketing" />
        <div className="divide-y divide-border">
          {hooks.map(h => (
            <div key={h.id} className="px-5 py-4">
              <p className="text-sm text-foreground leading-relaxed">{h.text}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {h.source && (
                  <span className="flex items-center gap-1 text-2xs font-medium text-muted-foreground">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary/60 inline-block" />
                    {bucketOf(h.source)}
                  </span>
                )}
                {(h.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
                {h.channel && <Tag>{h.channel}</Tag>}
              </div>
            </div>
          ))}
          {hooks.length === 0 && <EmptyState />}
        </div>
      </Card>
    </div>
  )
}

// ─── competitors page ────────────────────────────────────────────────────

function CompetitorsPage({ data, search }) {
  const complaints = useMemo(() => {
    let items = data?.competitor_complaints || []
    if (search) items = items.filter(c =>
      (c.tool || c.competitor || c.name || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.complaint || c.text || '').toLowerCase().includes(search.toLowerCase())
    )
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="Competitor Complaints" count={complaints.length} description="Weaknesses found across community & reviews" />
        <div className="divide-y divide-border">
          {complaints.map((c, i) => (
            <div key={c.id || i} className="px-5 py-3">
              <div className="flex items-start gap-4">
                <span className="text-xs font-semibold text-foreground w-24 pt-0.5 shrink-0">{c.tool || c.competitor || c.name}</span>
                <p className="text-sm text-muted-foreground flex-1">{c.complaint || c.text}</p>
                <div className="flex items-center gap-1.5 shrink-0">
                  {c.source && <Tag>{bucketOf(c.source)}</Tag>}
                  {(c.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
                </div>
              </div>
            </div>
          ))}
          {complaints.length === 0 && <EmptyState />}
        </div>
      </Card>
    </div>
  )
}

// ─── citations page ──────────────────────────────────────────────────────

function CitationsPage({ data, search }) {
  const citations = useMemo(() => {
    let items = data?.ai_citations || []
    if (search) items = items.filter(c => c.query?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="AI Citations" count={citations.length} description="FrontlineHQ visibility in AI engine responses" />
        {citations.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <Brain size={20} className="mx-auto mb-3 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">No AI citation checks yet.</p>
            <p className="text-xs text-muted-foreground mt-1">Run the pipeline to populate this section.</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {citations.map((c, i) => (
              <div key={c.id || i} className="px-5 py-4">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <p className="text-sm font-medium text-foreground">{c.query}</p>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Tag>{c.model}</Tag>
                    {c.frontlinehq_appears === true
                      ? <Tag variant="green">✓ Cited</Tag>
                      : <Tag variant="red">✗ Not cited</Tag>
                    }
                  </div>
                </div>
                {c.response_preview && (
                  <p className="text-xs text-muted-foreground italic leading-relaxed line-clamp-2 mb-2">{c.response_preview}</p>
                )}
                {c.competitors_cited?.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-2xs text-muted-foreground">Competitors:</span>
                    {c.competitors_cited.map(n => <Tag key={n}>{n}</Tag>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

// ─── hypotheses page ─────────────────────────────────────────────────────

function HypothesesPage({ data, search, teamFilter }) {
  const hyps = useMemo(() => {
    let items = data?.hypotheses || []
    if (teamFilter) items = items.filter(h => h.teams?.includes(teamFilter))
    if (search) items = items.filter(h =>
      (h.hypothesis || '').toLowerCase().includes(search.toLowerCase()) ||
      (h.action || '').toLowerCase().includes(search.toLowerCase())
    )
    return items
  }, [data, search, teamFilter])

  return (
    <div className="p-6 space-y-3">
      {hyps.map(h => (
        <Card key={h.id}>
          <div className="p-6">
            <p className="text-sm text-foreground leading-relaxed">{h.hypothesis}</p>
            <div className="flex items-center gap-1.5 mt-3">
              {(h.teams || []).map(t => <Tag key={t}>{t}</Tag>)}
              {h.strength === 'strong' && <Tag variant="green">strong</Tag>}
              {h.status && <Tag>{h.status}</Tag>}
              {fmtDate(h.generated_date) && (
                <span className="text-2xs text-muted-foreground ml-auto">{fmtDate(h.generated_date)}</span>
              )}
            </div>
          </div>
          {(h.action || h.metric) && (
            <div className="border-t border-border divide-y divide-border">
              {h.action && (
                <div className="px-5 py-3">
                  <p className="text-2xs text-muted-foreground uppercase tracking-widest mb-1.5">Action</p>
                  <p className="text-xs text-foreground leading-relaxed">{h.action}</p>
                </div>
              )}
              {h.metric && (
                <div className="px-5 py-3">
                  <p className="text-2xs text-muted-foreground uppercase tracking-widest mb-1.5">Success metric</p>
                  <p className="text-xs text-foreground leading-relaxed">{h.metric}</p>
                </div>
              )}
            </div>
          )}
        </Card>
      ))}
      {hyps.length === 0 && (
        <Card><EmptyState /></Card>
      )}
    </div>
  )
}

// ─── fanout page ─────────────────────────────────────────────────────────

function FanoutPage({ data, search }) {
  const terms = useMemo(() => {
    let items = data?.fanout_terms || []
    if (search) items = items.filter(t => (t.term || '').toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="Fanout Terms" count={terms.length} description="Background queries AI engines expand to" />
        <div className="divide-y divide-border">
          {terms.map((t, i) => (
            <div key={t.id || i} className="px-5 py-3 flex items-start gap-4">
              <p className="text-sm text-foreground flex-1">{t.term}</p>
              <div className="flex items-center gap-1.5 shrink-0">
                {(t.teams || []).map(tm => <Tag key={tm}>{tm}</Tag>)}
                {t.frontlinehq_present === false && <Tag variant="red">gap</Tag>}
              </div>
            </div>
          ))}
          {terms.length === 0 && <EmptyState />}
        </div>
      </Card>
    </div>
  )
}

// ─── queries page ────────────────────────────────────────────────────────

function QueriesPage({ data, search }) {
  const queries = useMemo(() => {
    let items = data?.next_queries || []
    if (search) items = items.filter(q => (q.query || '').toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <Card>
        <SectionHeader title="Next Queries" count={queries.length} description="Queued for next pipeline run" />
        <div className="divide-y divide-border">
          {queries.map((q, i) => (
            <div key={q.id || i} className="px-5 py-3">
              <p className="text-sm text-foreground">{q.query}</p>
              {q.rationale && <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{q.rationale}</p>}
              <div className="flex items-center gap-1.5 mt-2">
                {q.used === false && <Tag variant="amber">unused</Tag>}
                {fmtDate(q.generated_date) && (
                  <span className="text-2xs text-muted-foreground ml-auto">{fmtDate(q.generated_date)}</span>
                )}
              </div>
            </div>
          ))}
          {queries.length === 0 && <EmptyState />}
        </div>
      </Card>
    </div>
  )
}

// ─── transcripts page ────────────────────────────────────────────────────

function TranscriptsPage({ data, search }) {
  const calls = useMemo(() => {
    let items = data?.sales_calls || []
    if (search) items = items.filter(c =>
      (c.prospect || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.signal || '').toLowerCase().includes(search.toLowerCase())
    )
    return items
  }, [data, search])

  return (
    <div className="p-6 space-y-3">
      {calls.map((c, i) => (
        <Card key={c.id || i}>
          <div className="p-6">
            <div className="flex items-start justify-between gap-3 mb-3">
              <p className="text-sm font-semibold text-foreground">{c.prospect || `Call ${i + 1}`}</p>
              <div className="flex items-center gap-1.5 shrink-0">
                {c.stage && <Tag>{c.stage}</Tag>}
                {c.outcome && <Tag variant={c.outcome === 'won' ? 'green' : 'red'}>{c.outcome}</Tag>}
              </div>
            </div>
            {c.signal && (
              <p className="text-xs text-muted-foreground leading-relaxed italic mb-3">{c.signal}</p>
            )}
            {c.key_phrases?.length > 0 && (
              <div>
                <p className="text-2xs text-muted-foreground uppercase tracking-widest mb-2">Key phrases</p>
                <div className="space-y-1.5">
                  {c.key_phrases.slice(0, 4).map((p, j) => (
                    <p key={j} className="text-xs text-foreground pl-3 border-l border-border leading-relaxed">"{p}"</p>
                  ))}
                  {c.key_phrases.length > 4 && (
                    <p className="text-2xs text-muted-foreground pl-3">+{c.key_phrases.length - 4} more</p>
                  )}
                </div>
              </div>
            )}
          </div>
          {c.objections?.length > 0 && (
            <div className="border-t border-border px-5 py-3">
              <p className="text-2xs text-muted-foreground uppercase tracking-widest mb-2">Objections</p>
              <div className="space-y-1.5">
                {c.objections.map((o, j) => (
                  <p key={j} className="text-xs text-muted-foreground pl-3 border-l border-red-200 leading-relaxed">{o}</p>
                ))}
              </div>
            </div>
          )}
          <div className="border-t border-border px-5 py-2.5">
            <span className="text-2xs text-muted-foreground">{fmtDate(c.date)}</span>
          </div>
        </Card>
      ))}
      {calls.length === 0 && <Card><EmptyState /></Card>}
    </div>
  )
}

// ─── empty state ─────────────────────────────────────────────────────────

function EmptyState() {
  return <div className="px-5 py-10 text-center text-xs text-muted-foreground">No data</div>
}

// ─── page meta ───────────────────────────────────────────────────────────

const PAGE_META = {
  overview:    'Overview',
  icp:         'ICP Phrases',
  hooks:       'Outbound Hooks',
  competitors: 'Competitors',
  citations:   'AI Citations',
  hypotheses:  'Hypotheses',
  fanout:      'Fanout Terms',
  queries:     'Next Queries',
  transcripts: 'Sales Calls',
}

// ─── app ─────────────────────────────────────────────────────────────────

export default function App() {
  const { data, loading, error } = useData()
  const [active, setActive] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [teamFilter, setTeamFilter] = useState(null)
  const [pageSearch, setPageSearch] = useState('')

  const handleSetActive = (page) => {
    setActive(page)
    setTeamFilter(null)
    setPageSearch('')
  }

  const hasTeamFilter = ['icp', 'hooks', 'hypotheses'].includes(active)

  const renderPage = () => {
    if (loading) return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-muted-foreground animate-pulse">Loading…</p>
      </div>
    )
    if (error) return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-destructive">Error: {error}</p>
      </div>
    )
    switch (active) {
      case 'overview':    return <OverviewPage data={data} />
      case 'icp':         return <IcpPage data={data} search={pageSearch} teamFilter={teamFilter} />
      case 'hooks':       return <HooksPage data={data} search={pageSearch} teamFilter={teamFilter} />
      case 'competitors': return <CompetitorsPage data={data} search={pageSearch} />
      case 'citations':   return <CitationsPage data={data} search={pageSearch} />
      case 'hypotheses':  return <HypothesesPage data={data} search={pageSearch} teamFilter={teamFilter} />
      case 'fanout':      return <FanoutPage data={data} search={pageSearch} />
      case 'queries':     return <QueriesPage data={data} search={pageSearch} />
      case 'transcripts': return <TranscriptsPage data={data} search={pageSearch} />
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar active={active} setActive={handleSetActive} open={sidebarOpen} setOpen={setSidebarOpen} data={data} />
      <div className="lg:pl-[200px] flex flex-col min-h-screen">
        <TopBar
          title={PAGE_META[active]}
          data={data}
          onNavigate={handleSetActive}
          teamFilter={hasTeamFilter ? teamFilter : undefined}
          setTeamFilter={hasTeamFilter ? setTeamFilter : undefined}
          showTeamFilter={hasTeamFilter}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className="flex-1">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}
