import { useState, useEffect, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
  LayoutDashboard, MessageSquare, Zap, Users, Lightbulb, Search,
  TrendingUp, FileText, Globe, Menu, Brain, Building2, Hash, Filter
} from 'lucide-react'

// ─── helpers ────────────────────────────────────────────────────────────────

const ALL_TEAMS = ['Sales', 'Product', 'Social', 'CS', 'Leadership']

function fmtDate(d) {
  if (!d) return '—'
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

function useData() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/data')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  return { data, loading, error }
}

// ─── sidebar nav ────────────────────────────────────────────────────────────

const NAV = [
  { id: 'overview',     label: 'Overview',       icon: LayoutDashboard },
  { id: 'icp',          label: 'ICP Phrases',     icon: MessageSquare },
  { id: 'hooks',        label: 'Outbound Hooks',  icon: Zap },
  { id: 'competitors',  label: 'Competitors',     icon: Building2 },
  { id: 'citations',    label: 'AI Citations',    icon: Brain },
  { id: 'hypotheses',   label: 'Hypotheses',      icon: Lightbulb },
  { id: 'fanout',       label: 'Fanout Terms',    icon: TrendingUp },
  { id: 'queries',      label: 'Next Queries',    icon: Search },
  { id: 'transcripts',  label: 'Sales Calls',     icon: FileText },
]

function Sidebar({ active, setActive, open, setOpen }) {
  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black/30 z-20 lg:hidden" onClick={() => setOpen(false)} />
      )}
      <aside className={`
        fixed top-0 left-0 h-full z-30 flex flex-col
        w-[220px] bg-white border-r border-border
        transition-transform duration-200
        ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="px-5 py-6 border-b border-border">
          <div className="leading-none">
            <span className="font-heading font-bold text-xl text-foreground tracking-tight">FrontlineHQ</span>
          </div>
          <div className="mt-0.5">
            <span className="font-heading text-[11px] text-muted-foreground tracking-widest uppercase">AEO / GEO Bank</span>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-3 px-2">
          {NAV.map(item => {
            const Icon = item.icon
            const isActive = active === item.id
            return (
              <button
                key={item.id}
                onClick={() => { setActive(item.id); setOpen(false) }}
                className={`
                  w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-nav font-medium mb-0.5
                  transition-colors text-left
                  ${isActive
                    ? 'bg-primary/10 text-primary border-l-2 border-primary pl-[10px]'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }
                `}
              >
                <Icon size={15} />
                {item.label}
              </button>
            )
          })}
        </nav>
        <div className="px-5 py-4 border-t border-border">
          <p className="text-[10px] text-muted-foreground">AEO Intelligence Pipeline</p>
        </div>
      </aside>
    </>
  )
}

// ─── top bar ────────────────────────────────────────────────────────────────

function TopBar({ title, subtitle, search, setSearch, teamFilter, setTeamFilter, onMenuClick }) {
  return (
    <header className="sticky top-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border px-6 py-3">
      <div className="flex items-center gap-3">
        <button onClick={onMenuClick} className="lg:hidden p-1.5 rounded-md hover:bg-muted">
          <Menu size={18} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="font-heading font-bold text-lg leading-tight truncate">{title}</h1>
          {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
        </div>
        {setSearch && (
          <div className="hidden sm:flex items-center gap-2">
            <div className="relative">
              <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-8 h-8 w-48 text-xs"
              />
            </div>
          </div>
        )}
      </div>
      {setTeamFilter && (
        <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide mr-1 flex items-center gap-1"><Filter size={10}/>Team</span>
          {['All', ...ALL_TEAMS].map(t => (
            <button
              key={t}
              onClick={() => setTeamFilter(t === 'All' ? null : t)}
              className={`px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors ${
                (t === 'All' && !teamFilter) || teamFilter === t
                  ? 'bg-primary text-white border-primary'
                  : 'bg-white text-muted-foreground border-border hover:border-primary hover:text-primary'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}
    </header>
  )
}

// ─── stat card ──────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, highlight }) {
  return (
    <Card className={`p-5 ${highlight ? 'border-primary/40 bg-primary/5' : ''}`}>
      <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-heading font-bold text-4xl leading-none tracking-tight ${highlight ? 'text-primary' : 'text-foreground'}`}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </Card>
  )
}

// ─── bar chart ──────────────────────────────────────────────────────────────

function BarChart({ data, valueKey = 'count', labelKey = 'name' }) {
  const maxVal = Math.max(...data.map(d => d[valueKey] || 0), 1)
  return (
    <div className="space-y-2">
      {data.map((row, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="w-36 text-xs text-muted-foreground truncate shrink-0">{row[labelKey]}</span>
          <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${Math.round((row[valueKey] / maxVal) * 100)}%` }}
            />
          </div>
          <span className="text-xs font-medium w-6 text-right text-foreground">{row[valueKey]}</span>
        </div>
      ))}
    </div>
  )
}

// ─── overview page ──────────────────────────────────────────────────────────

function OverviewPage({ data }) {
  const citationRate = useMemo(() => {
    const items = data?.ai_citations || []
    if (!items.length) return null
    const cited = items.filter(c => c.frontlinehq_appears === true).length
    return Math.round((cited / items.length) * 100)
  }, [data])

  const stats = useMemo(() => {
    if (!data) return []
    return [
      {
        label: 'Citation Rate',
        value: citationRate !== null ? `${citationRate}%` : '—',
        sub: citationRate !== null ? `${data.ai_citations.filter(c=>c.frontlinehq_appears===true).length} of ${data.ai_citations.length} AI queries` : 'Run pipeline to check',
        highlight: true,
      },
      { label: 'ICP Phrases',    value: data.icp_phrases?.length || 0 },
      { label: 'Outbound Hooks', value: data.outbound_hooks?.length || 0 },
      { label: 'Hypotheses',     value: data.hypotheses?.length || 0 },
      { label: 'Fanout Terms',   value: data.fanout_terms?.length || 0 },
      { label: 'Sales Calls',    value: data.sales_calls?.length || 0 },
    ]
  }, [data, citationRate])

  const competitorCounts = useMemo(() => {
    if (!data) return []
    const counts = {}
    ;(data.competitor_complaints || []).forEach(c => {
      const name = c.tool || c.competitor || c.name
      if (name) counts[name] = (counts[name] || 0) + 1
    })
    ;(data.citations || []).forEach(c => {
      ;(c.competitors_cited || []).forEach(name => { counts[name] = (counts[name] || 0) + 1 })
    })
    ;(data.ai_citations || []).forEach(c => {
      ;(c.competitors_cited || []).forEach(name => { counts[name] = (counts[name] || 0) + 1 })
    })
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
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
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map(s => <StatCard key={s.label} {...s} />)}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {competitorCounts.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Competitor Landscape</CardTitle>
              <CardDescription>Mentions across all data sources</CardDescription>
            </CardHeader>
            <CardContent>
              <BarChart data={competitorCounts} />
            </CardContent>
          </Card>
        )}
        {sourceCounts.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">ICP Source Breakdown</CardTitle>
              <CardDescription>Where language was found</CardDescription>
            </CardHeader>
            <CardContent>
              <BarChart data={sourceCounts} />
            </CardContent>
          </Card>
        )}
      </div>

      {citationRows.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">AI Engine Citation Grid</CardTitle>
            <CardDescription>Does FrontlineHQ appear in AI engine responses?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 pr-4 text-xs font-medium text-muted-foreground">Query</th>
                    {['perplexity', 'claude'].map(m => (
                      <th key={m} className="text-center py-2 px-3 text-xs font-medium text-muted-foreground capitalize">{m}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {citationRows.map((row, i) => (
                    <tr key={i} className="border-b border-border/50 last:border-0">
                      <td className="py-2 pr-4 text-xs text-muted-foreground max-w-[280px] truncate">{row.query}</td>
                      {['perplexity', 'claude'].map(m => (
                        <td key={m} className="py-2 px-3 text-center">
                          {row.models[m] === undefined
                            ? <span className="text-muted-foreground text-xs">—</span>
                            : row.models[m]
                              ? <span className="text-emerald-600 font-bold">✓</span>
                              : <span className="text-red-400 font-bold">✗</span>
                          }
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {data.icp_phrases?.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Top ICP Phrases</CardTitle>
            <CardDescription>Highest-signal language from customers</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.icp_phrases.slice(0, 6).map(p => (
                <div key={p.id} className="flex items-start gap-3 p-3 rounded-md bg-muted/50">
                  <span className="shrink-0 mt-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wide w-14">{p.source}</span>
                  <span className="text-sm text-foreground flex-1">"{p.text}"</span>
                  <div className="flex gap-1 shrink-0">
                    {(p.teams || []).slice(0, 2).map(t => (
                      <span key={t} className="text-[10px] text-muted-foreground border border-border rounded px-1.5 py-0.5">{t}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {data.hypotheses?.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Latest Hypotheses</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.hypotheses.slice(0, 3).map(h => (
                <div key={h.id} className="p-4 rounded-md border border-border">
                  <div className="flex items-start gap-2 mb-2">
                    <Lightbulb size={14} className="text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-sm text-foreground leading-relaxed">{h.hypothesis}</p>
                  </div>
                  <div className="flex gap-2 mt-2 pl-5">
                    {(h.teams || []).map(t => (
                      <span key={t} className="text-[10px] text-muted-foreground border border-border rounded px-1.5 py-0.5">{t}</span>
                    ))}
                    {h.strength && <span className="text-[10px] text-muted-foreground border border-border rounded px-1.5 py-0.5">{h.strength}</span>}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ─── icp page ────────────────────────────────────────────────────────────────

function IcpPage({ data, search, teamFilter }) {
  const phrases = useMemo(() => {
    let items = data?.icp_phrases || []
    if (teamFilter) items = items.filter(p => p.teams?.includes(teamFilter))
    if (search) items = items.filter(p => p.text?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search, teamFilter])

  return (
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{phrases.length} phrases</div>
      <div className="space-y-2">
        {phrases.map(p => (
          <div key={p.id} className="p-4 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <p className="text-sm text-foreground mb-2">"{p.text}"</p>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{bucketOf(p.source)}</span>
              {p.geography && p.geography !== 'Unknown' && (
                <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{p.geography}</span>
              )}
              {(p.teams || []).map(t => (
                <span key={t} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{t}</span>
              ))}
              {p.hot && <span className="text-[10px] bg-emerald-100 text-emerald-700 rounded px-1.5 py-0.5">Hot</span>}
              <span className="text-[10px] text-muted-foreground ml-auto">{fmtDate(p.run_date)}</span>
            </div>
          </div>
        ))}
        {phrases.length === 0 && <EmptyState text="No ICP phrases found." />}
      </div>
    </div>
  )
}

// ─── hooks page ──────────────────────────────────────────────────────────────

function HooksPage({ data, search, teamFilter }) {
  const hooks = useMemo(() => {
    let items = data?.outbound_hooks || []
    if (teamFilter) items = items.filter(h => h.teams?.includes(teamFilter))
    if (search) items = items.filter(h => h.text?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search, teamFilter])

  return (
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{hooks.length} hooks</div>
      <div className="space-y-2">
        {hooks.map(h => (
          <div key={h.id} className="p-4 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <div className="flex items-start gap-2">
              <Zap size={13} className="text-primary shrink-0 mt-0.5" />
              <p className="text-sm text-foreground flex-1">{h.text}</p>
            </div>
            <div className="flex gap-2 mt-2 pl-5 flex-wrap">
              {(h.teams || []).map(t => (
                <span key={t} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{t}</span>
              ))}
              {h.channel && <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{h.channel}</span>}
              <span className="text-[10px] text-muted-foreground ml-auto">{fmtDate(h.run_date)}</span>
            </div>
          </div>
        ))}
        {hooks.length === 0 && <EmptyState text="No outbound hooks found." />}
      </div>
    </div>
  )
}

// ─── competitors page ────────────────────────────────────────────────────────

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
      <div className="text-xs text-muted-foreground mb-4">{complaints.length} entries</div>
      <div className="space-y-2">
        {complaints.map((c, i) => (
          <div key={c.id || i} className="p-4 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <div className="flex items-start gap-2 mb-2">
              <Building2 size={13} className="text-primary shrink-0 mt-0.5" />
              <span className="text-sm font-semibold text-primary">{c.tool || c.competitor || c.name}</span>
            </div>
            {(c.complaint || c.text) && (
              <p className="text-sm text-foreground ml-5">{c.complaint || c.text}</p>
            )}
            <div className="flex gap-2 mt-2 ml-5 flex-wrap">
              {c.source && <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{bucketOf(c.source)}</span>}
              {(c.teams || []).map(t => (
                <span key={t} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{t}</span>
              ))}
              <span className="text-[10px] text-muted-foreground ml-auto">{fmtDate(c.run_date)}</span>
            </div>
          </div>
        ))}
        {complaints.length === 0 && <EmptyState text="No competitor data found." />}
      </div>
    </div>
  )
}

// ─── citations page ──────────────────────────────────────────────────────────

function CitationsPage({ data, search }) {
  const citations = useMemo(() => {
    let items = data?.ai_citations || []
    if (search) items = items.filter(c => c.query?.toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{citations.length} checks</div>
      {citations.length === 0 && (
        <div className="rounded-lg border border-border p-8 text-center">
          <Brain size={24} className="mx-auto mb-3 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">No AI citation checks yet.</p>
          <p className="text-xs text-muted-foreground mt-1">Run the pipeline with a Perplexity or Claude API key to populate this.</p>
        </div>
      )}
      <div className="space-y-2">
        {citations.map((c, i) => (
          <div key={c.id || i} className="p-4 rounded-lg border border-border bg-card">
            <div className="flex items-start justify-between gap-3 mb-3">
              <p className="text-sm text-foreground font-medium">{c.query}</p>
              <div className="flex items-center gap-1.5 shrink-0">
                <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground capitalize">{c.model}</span>
                {c.frontlinehq_appears === true
                  ? <span className="text-[10px] bg-emerald-100 text-emerald-700 rounded px-1.5 py-0.5">✓ Cited</span>
                  : <span className="text-[10px] bg-red-50 text-red-500 border border-red-200 rounded px-1.5 py-0.5">✗ Not cited</span>
                }
              </div>
            </div>
            {c.response_preview && (
              <p className="text-xs text-muted-foreground italic border-l-2 border-border pl-3 mb-2 line-clamp-2">
                {c.response_preview}
              </p>
            )}
            {c.competitors_cited?.length > 0 && (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[10px] text-muted-foreground">Competitors:</span>
                {c.competitors_cited.map(n => (
                  <span key={n} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{n}</span>
                ))}
              </div>
            )}
            <div className="mt-2">
              <span className="text-[10px] text-muted-foreground">{fmtDate(c.date || c.run_date)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── hypotheses page ─────────────────────────────────────────────────────────

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
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{hyps.length} hypotheses</div>
      <div className="space-y-4">
        {hyps.map(h => (
          <div key={h.id} className="rounded-lg border border-border bg-card overflow-hidden">
            <div className="p-5">
              <div className="flex items-start gap-3 mb-3">
                <Lightbulb size={16} className="text-amber-500 shrink-0 mt-0.5" />
                <p className="text-sm text-foreground leading-relaxed">{h.hypothesis}</p>
              </div>
              {h.action && (
                <div className="mt-3 pl-7">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1">Action</p>
                  <p className="text-xs text-foreground leading-relaxed">{h.action}</p>
                </div>
              )}
              {h.metric && (
                <div className="mt-3 pl-7">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-1">Success Metric</p>
                  <p className="text-xs text-foreground leading-relaxed">{h.metric}</p>
                </div>
              )}
            </div>
            <div className="px-5 py-3 border-t border-border bg-muted/30 flex items-center gap-2 flex-wrap">
              {(h.teams || []).map(t => (
                <span key={t} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground bg-white">{t}</span>
              ))}
              {h.strength && (
                <span className={`text-[10px] rounded px-1.5 py-0.5 border ${
                  h.strength === 'strong' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'border-border text-muted-foreground bg-white'
                }`}>{h.strength}</span>
              )}
              {h.status && (
                <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground bg-white">{h.status}</span>
              )}
              <span className="text-[10px] text-muted-foreground ml-auto">{fmtDate(h.generated_date)}</span>
            </div>
          </div>
        ))}
        {hyps.length === 0 && <EmptyState text="No hypotheses found." />}
      </div>
    </div>
  )
}

// ─── fanout page ─────────────────────────────────────────────────────────────

function FanoutPage({ data, search }) {
  const terms = useMemo(() => {
    let items = data?.fanout_terms || []
    if (search) items = items.filter(t => (t.term || '').toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{terms.length} terms</div>
      <div className="space-y-2">
        {terms.map((t, i) => (
          <div key={t.id || i} className="flex items-start gap-3 p-3 rounded-md border border-border bg-card hover:border-primary/30 transition-colors">
            <TrendingUp size={13} className="text-muted-foreground shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground">{t.term}</p>
              {t.query && <p className="text-xs text-muted-foreground mt-0.5">From: "{t.query}"</p>}
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {(t.teams || []).map(tm => (
                <span key={tm} className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground">{tm}</span>
              ))}
              {t.frontlinehq_present === false && (
                <span className="text-[10px] bg-red-50 text-red-400 border border-red-200 rounded px-1.5 py-0.5">gap</span>
              )}
            </div>
          </div>
        ))}
        {terms.length === 0 && <EmptyState text="No fanout terms found." />}
      </div>
    </div>
  )
}

// ─── queries page ────────────────────────────────────────────────────────────

function QueriesPage({ data, search }) {
  const queries = useMemo(() => {
    let items = data?.next_queries || []
    if (search) items = items.filter(q => (q.query || '').toLowerCase().includes(search.toLowerCase()))
    return items
  }, [data, search])

  return (
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{queries.length} queries queued</div>
      <div className="space-y-2">
        {queries.map((q, i) => (
          <div key={q.id || i} className="p-4 rounded-lg border border-border bg-card hover:border-primary/30 transition-colors">
            <div className="flex items-start gap-3 mb-2">
              <Search size={13} className="text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-sm text-foreground">{q.query}</p>
            </div>
            {q.rationale && (
              <p className="text-xs text-muted-foreground pl-7 leading-relaxed">{q.rationale}</p>
            )}
            <div className="flex items-center gap-2 mt-2 pl-7">
              {q.used === false && <span className="text-[10px] bg-amber-50 text-amber-600 border border-amber-200 rounded px-1.5 py-0.5">unused</span>}
              <span className="text-[10px] text-muted-foreground ml-auto">{fmtDate(q.generated_date)}</span>
            </div>
          </div>
        ))}
        {queries.length === 0 && <EmptyState text="No next queries found." />}
      </div>
    </div>
  )
}

// ─── transcripts page ────────────────────────────────────────────────────────

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
    <div className="p-6">
      <div className="text-xs text-muted-foreground mb-4">{calls.length} transcripts</div>
      <div className="space-y-4">
        {calls.map((c, i) => (
          <Card key={c.id || i} className="overflow-hidden">
            <div className="p-5">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <FileText size={14} className="text-primary shrink-0" />
                  <span className="text-sm font-semibold">{c.prospect || `Call ${i + 1}`}</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {c.stage && <span className="text-[10px] border border-border rounded px-1.5 py-0.5 text-muted-foreground capitalize">{c.stage}</span>}
                  {c.outcome && (
                    <span className={`text-[10px] rounded px-1.5 py-0.5 border ${
                      c.outcome === 'won' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-500 border-red-200'
                    }`}>{c.outcome}</span>
                  )}
                </div>
              </div>
              {c.signal && (
                <p className="text-xs text-muted-foreground leading-relaxed mb-3 pl-6 italic">{c.signal}</p>
              )}
              {c.key_phrases?.length > 0 && (
                <div className="pl-6 space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Key phrases</p>
                  {c.key_phrases.slice(0, 4).map((p, j) => (
                    <p key={j} className="text-xs text-foreground border-l-2 border-primary/30 pl-2 leading-relaxed">"{p}"</p>
                  ))}
                  {c.key_phrases.length > 4 && (
                    <p className="text-[10px] text-muted-foreground pl-2">+{c.key_phrases.length - 4} more</p>
                  )}
                </div>
              )}
              {c.objections?.length > 0 && (
                <div className="pl-6 mt-3 space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Objections</p>
                  {c.objections.map((o, j) => (
                    <p key={j} className="text-xs text-foreground border-l-2 border-red-200 pl-2 leading-relaxed">{o}</p>
                  ))}
                </div>
              )}
            </div>
            <div className="px-5 py-3 border-t border-border bg-muted/30">
              <span className="text-[10px] text-muted-foreground">{fmtDate(c.date)}</span>
            </div>
          </Card>
        ))}
        {calls.length === 0 && <EmptyState text="No sales call transcripts found." />}
      </div>
    </div>
  )
}

// ─── empty state ────────────────────────────────────────────────────────────

function EmptyState({ text }) {
  return (
    <div className="text-center py-12 text-muted-foreground text-sm">{text}</div>
  )
}

// ─── page meta ───────────────────────────────────────────────────────────────

const PAGE_META = {
  overview:    { title: 'Overview',           subtitle: 'AEO Intelligence summary' },
  icp:         { title: 'ICP Phrases',         subtitle: 'Customer language from community & reviews' },
  hooks:       { title: 'Outbound Hooks',      subtitle: 'Message angles for sales & marketing' },
  competitors: { title: 'Competitors',         subtitle: 'Competitor complaints and mentions' },
  citations:   { title: 'AI Citations',        subtitle: 'FrontlineHQ visibility in AI engines' },
  hypotheses:  { title: 'Hypotheses',          subtitle: 'Strategic hypotheses generated by pipeline' },
  fanout:      { title: 'Fanout Terms',        subtitle: 'Background queries AI engines expand to' },
  queries:     { title: 'Next Queries',        subtitle: 'Queued for next pipeline run' },
  transcripts: { title: 'Sales Calls',         subtitle: 'Phrases extracted from transcripts' },
}

// ─── main app ────────────────────────────────────────────────────────────────

export default function App() {
  const { data, loading, error } = useData()
  const [active, setActive] = useState('overview')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [teamFilter, setTeamFilter] = useState(null)

  const handleSetActive = (page) => {
    setActive(page)
    setSearch('')
    setTeamFilter(null)
  }

  const meta = PAGE_META[active] || { title: active }
  const hasTeamFilter = ['icp', 'hooks', 'hypotheses'].includes(active)
  const hasSearch = active !== 'overview'

  const renderPage = () => {
    if (loading) return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground text-sm animate-pulse">Loading intelligence bank…</div>
      </div>
    )
    if (error) return (
      <div className="flex items-center justify-center h-64">
        <div className="text-destructive text-sm">Error: {error}</div>
      </div>
    )
    switch (active) {
      case 'overview':    return <OverviewPage data={data} />
      case 'icp':         return <IcpPage data={data} search={search} teamFilter={teamFilter} />
      case 'hooks':       return <HooksPage data={data} search={search} teamFilter={teamFilter} />
      case 'competitors': return <CompetitorsPage data={data} search={search} />
      case 'citations':   return <CitationsPage data={data} search={search} />
      case 'hypotheses':  return <HypothesesPage data={data} search={search} teamFilter={teamFilter} />
      case 'fanout':      return <FanoutPage data={data} search={search} />
      case 'queries':     return <QueriesPage data={data} search={search} />
      case 'transcripts': return <TranscriptsPage data={data} search={search} />
      default:            return null
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar active={active} setActive={handleSetActive} open={sidebarOpen} setOpen={setSidebarOpen} />
      <div className="lg:pl-[220px] flex flex-col min-h-screen">
        <TopBar
          title={meta.title}
          subtitle={meta.subtitle}
          search={hasSearch ? search : undefined}
          setSearch={hasSearch ? setSearch : undefined}
          teamFilter={hasTeamFilter ? teamFilter : undefined}
          setTeamFilter={hasTeamFilter ? setTeamFilter : undefined}
          onMenuClick={() => setSidebarOpen(true)}
        />
        <main className="flex-1">{renderPage()}</main>
        {data?.meta && (
          <footer className="px-6 py-3 border-t border-border text-[10px] text-muted-foreground flex items-center gap-3">
            <span>Last run: {fmtDate(data.meta.last_run)}</span>
            <span>·</span>
            <span>{data.meta.run_count} total runs</span>
            <span>·</span>
            <span>{(data.meta.markets || []).join(', ')}</span>
          </footer>
        )}
      </div>
    </div>
  )
}
