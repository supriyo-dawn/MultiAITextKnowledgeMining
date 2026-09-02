import { useState } from 'react'
import { useKnowledge } from '../context/KnowledgeContext'

const nodePresets = [
  { label: 'Strategy', x: '18%', y: '35%', size: 'h-14 w-14', tone: 'bg-[#171513] text-[#f5efe8]' },
  { label: 'Pricing', x: '42%', y: '16%', size: 'h-16 w-16', tone: 'bg-[#d7b79c] text-[#171513]' },
  { label: 'Risk', x: '62%', y: '38%', size: 'h-14 w-14', tone: 'bg-[#f2e6d7] text-[#171513]' },
  { label: 'Markets', x: '75%', y: '22%', size: 'h-14 w-14', tone: 'bg-[#171513] text-[#f5efe8]' },
  { label: 'Ops', x: '56%', y: '70%', size: 'h-14 w-14', tone: 'bg-[#d7b79c] text-[#171513]' },
]

export default function Knowledge() {
  const { relations, addRelation, exportGraph } = useKnowledge()
  const [form, setForm] = useState({ subject: 'Strategy', relation: 'influences', object: 'Pricing', confidence: '0.93' })

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    addRelation({
      subject: form.subject.trim() || 'New entity',
      relation: form.relation.trim() || 'relates to',
      object: form.object.trim() || 'Related entity',
      confidence: Number(form.confidence) || 0.5,
    })
    setForm({ subject: '', relation: '', object: '', confidence: '0.8' })
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#fffaf4] p-6 md:p-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-[#72685c]">Graph explorer</p>
            <h2 className="editorial-display mt-2 text-4xl text-[#171513]">Knowledge network</h2>
          </div>

          <button onClick={exportGraph} className="rounded-full border border-[#d0c4b7] bg-white px-4 py-2 text-sm font-medium text-[#171513]">
            Export graph
          </button>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[28px] border border-[#d9d0c5] bg-[#f9f4ee] p-5">
          <div className="relative h-[440px] overflow-hidden rounded-[24px] border border-[#e5dcca] bg-[linear-gradient(150deg,#f7f2eb_0%,#efe7dc_100%)]">
            <svg className="absolute inset-0 h-full w-full" viewBox="0 0 800 440" preserveAspectRatio="none">
              <path d="M200 170 L330 105 L470 180" stroke="#c3a78d" strokeWidth="2" fill="none" />
              <path d="M330 105 L520 115" stroke="#c3a78d" strokeWidth="2" fill="none" />
              <path d="M330 105 L390 270" stroke="#c3a78d" strokeWidth="2" fill="none" />
              <path d="M470 180 L610 250" stroke="#c3a78d" strokeWidth="2" fill="none" />
              <path d="M390 270 L570 310" stroke="#c3a78d" strokeWidth="2" fill="none" />
              <path d="M520 115 L610 250" stroke="#c3a78d" strokeWidth="2" fill="none" />
            </svg>

            {nodePresets.map((node) => (
              <div
                key={node.label}
                className={`absolute ${node.size} ${node.tone} flex items-center justify-center rounded-full border border-[#d1b79d] text-xs font-medium shadow-[0_10px_30px_rgba(32,24,18,0.12)]`}
                style={{ left: node.x, top: node.y, transform: 'translate(-50%, -50%)' }}
              >
                {node.label}
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
            <h3 className="text-lg font-semibold text-[#171513]">Connected entities</h3>
            <div className="mt-5 space-y-3">
              {relations.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-[#d9d0c5] bg-[#faf7f3] p-4 text-sm text-[#5f564f]">
                  No relationships yet. Add one to the graph below.
                </div>
              ) : (
                relations.map((relation) => (
                  <div key={relation.id} className="rounded-2xl border border-[#ece1d5] bg-[#faf7f3] p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div className="text-sm font-medium text-[#171513]">{relation.subject}</div>
                      <div className="text-xs uppercase tracking-[0.18em] text-[#7a5a3d]">{relation.relation}</div>
                    </div>
                    <div className="mt-2 text-sm text-[#5f564f]">{relation.object}</div>
                    <div className="mt-3 flex items-center justify-between text-xs uppercase tracking-[0.18em] text-[#71675f]">
                      <span>Confidence</span>
                      <span>{relation.confidence.toFixed(2)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="rounded-[28px] border border-[#d9d0c5] bg-[#f7f2ed] p-6">
            <h3 className="text-lg font-semibold text-[#171513]">Add relationship</h3>
            <div className="mt-4 space-y-3">
              <input
                value={form.subject}
                onChange={(event) => setForm((current) => ({ ...current, subject: event.target.value }))}
                placeholder="Subject"
                className="w-full rounded-2xl border border-[#d7c8b8] bg-white px-3 py-2 text-sm outline-none"
              />
              <input
                value={form.relation}
                onChange={(event) => setForm((current) => ({ ...current, relation: event.target.value }))}
                placeholder="Relation"
                className="w-full rounded-2xl border border-[#d7c8b8] bg-white px-3 py-2 text-sm outline-none"
              />
              <input
                value={form.object}
                onChange={(event) => setForm((current) => ({ ...current, object: event.target.value }))}
                placeholder="Object"
                className="w-full rounded-2xl border border-[#d7c8b8] bg-white px-3 py-2 text-sm outline-none"
              />
              <input
                value={form.confidence}
                onChange={(event) => setForm((current) => ({ ...current, confidence: event.target.value }))}
                placeholder="Confidence (0.0 - 1.0)"
                className="w-full rounded-2xl border border-[#d7c8b8] bg-white px-3 py-2 text-sm outline-none"
              />
            </div>
            <button type="submit" className="mt-4 rounded-full bg-[#171513] px-5 py-2.5 text-sm font-medium text-[#f7f3ee]">
              Save relationship
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
