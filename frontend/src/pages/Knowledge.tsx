import { useEffect, useState } from 'react'

export default function Knowledge() {
  const [graph, setGraph] = useState<{ available: boolean; nodes: Entity[]; edges: Relationship[] } | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/knowledge/graph')
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load knowledge graph')
        return response.json() as Promise<{ available: boolean; nodes: Entity[]; edges: Relationship[] }>
      })
      .then(setGraph)
      .catch((loadError: Error) => setError(loadError.message))
  }, [])

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="rounded-2xl border border-[#dfe6df] bg-white/85 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.05)]">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#167c78]">Graph desk</p>
        <h2 className="mb-2 font-serif text-2xl font-semibold text-[#17212b]">Knowledge graph</h2>
        {error ? <p className="text-sm text-red-600">{error}</p> : (
          <p className="text-sm text-[#718078]">
            {graph === null ? 'Checking graph availability...' : graph.available ? `${graph.nodes.length} entities connected by ${graph.edges.length} relationships.` : 'Graph services are not configured yet.'}
          </p>
        )}
      </div>
      {graph?.available && (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <GraphList title="Entities" items={graph.nodes.map((entity) => `${entity.text} · ${entity.label}`)} />
          <GraphList title="Relationships" items={graph.edges.map((edge) => `${edge.relation_type} · ${edge.evidence}`)} />
        </div>
      )}
    </div>
  )
}

interface Entity {
  text: string
  label: string
}

interface Relationship {
  relation_type: string
  evidence: string
}

function GraphList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-2xl border border-[#dfe6df] bg-white/85 p-5 shadow-[0_12px_30px_rgba(23,33,43,0.04)]">
      <h3 className="mb-3 font-semibold text-[#17212b]">{title}</h3>
      {items.length ? (
        <ul className="space-y-2 text-sm text-[#34443d]">
          {items.slice(0, 20).map((item, index) => <li key={`${item}-${index}`} className="rounded-lg bg-[#f3f7f3] px-3 py-2">{item}</li>)}
        </ul>
      ) : <p className="text-sm text-[#718078]">No data yet.</p>}
    </section>
  )
}
