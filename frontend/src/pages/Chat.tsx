import { useState } from 'react'

interface Source {
  chunk_id: string
  document_id: string
  text: string
}

export default function Chat() {
  const [question, setQuestion] = useState('')
  const [sources, setSources] = useState<Source[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const askQuestion = async () => {
    if (!question.trim()) return
    setError('')
    const response = await fetch('/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question.trim() }),
    })
    if (!response.ok) {
      setError('Unable to retrieve context')
      return
    }
    const data = await response.json()
    setMessage(data.message)
    setSources(data.sources)
  }

  return (
    <div className="mx-auto max-w-6xl animate-[fadeIn_420ms_ease-out]">
      <div className="rounded-2xl border border-[#dfe6df] bg-white/85 p-6 shadow-[0_18px_50px_rgba(23,33,43,0.05)]">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#167c78]">Question desk</p>
        <h2 className="mb-1 font-serif text-2xl font-semibold text-[#17212b]">Ask your documents</h2>
        <p className="mb-5 text-sm text-[#718078]">Retrieval is available now; LLM answer generation requires provider configuration.</p>
        <form className="flex gap-3" onSubmit={(event) => { event.preventDefault(); void askQuestion() }}>
          <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question" className="min-w-0 flex-1 rounded-md border border-[#cbd8d1] bg-[#f8faf8] px-3 py-3 text-sm outline-none transition focus:border-[#167c78] focus:ring-2 focus:ring-[#167c78]/15" />
          <button type="submit" disabled={!question.trim()} className="rounded-md bg-[#f47f68] px-5 py-2 text-sm font-semibold text-[#17212b] disabled:bg-[#dbe2dc]">Retrieve</button>
        </form>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        {message && <p className="mt-5 rounded-xl bg-[#e1f1ed] p-4 text-sm text-[#34534d]">{message}</p>}
        <div className="mt-5 space-y-3">
          {sources.map((source) => <article key={source.chunk_id} className="border-l-4 border-[#f47f68] pl-4 text-sm leading-6 text-[#34443d]">{source.text}<p className="mt-1 text-xs font-medium uppercase tracking-wider text-[#718078]">Document {source.document_id}</p></article>)}
        </div>
      </div>
    </div>
  )
}
