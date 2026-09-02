import { useState } from 'react'
import { useKnowledge } from '../context/KnowledgeContext'

const suggestedPrompts = ['How did the market change?', 'Who owns pricing risk?', 'Summarize the policy memo']

export default function Chat() {
  const { chatMessages, sendChatPrompt } = useKnowledge()
  const [draft, setDraft] = useState('Which sources confirm the pricing conclusion?')
  const [isSending, setIsSending] = useState(false)

  const handleSend = async (promptText?: string) => {
    const nextPrompt = (promptText ?? draft).trim()
    if (!nextPrompt) return

    setIsSending(true)
    try {
      await sendChatPrompt(nextPrompt)
      setDraft('')
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#f3eadf] p-6">
        <p className="text-[11px] uppercase tracking-[0.22em] text-[#72685c]">Assistant</p>
        <h2 className="editorial-display mt-2 text-4xl text-[#171513]">Question answering</h2>

        <div className="mt-6 space-y-3">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSend(prompt)}
              className="block w-full rounded-2xl border border-[#d8cbb9] bg-[#fffdf9] px-4 py-3 text-left text-sm text-[#171513] transition hover:border-[#b79f82]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-[28px] border border-[#d9d0c5] bg-[#ffffff] p-6">
        <div className="flex items-center justify-between border-b border-[#e7dccd] pb-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-[#72685c]">Live chat</p>
            <h3 className="mt-1 text-lg font-semibold text-[#171513]">Knowledge assistant</h3>
          </div>
          <span className="rounded-full bg-[#edf5ef] px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-[#406d42]">
            Online
          </span>
        </div>

        <div className="mt-5 space-y-4">
          {chatMessages.map((message) => (
            <div key={message.id} className={message.role === 'user' ? 'ml-auto max-w-[85%]' : 'max-w-[85%]'}>
              <div
                className={[
                  'rounded-[22px] px-4 py-3 text-sm leading-7',
                  message.role === 'user'
                    ? 'bg-[#171513] text-[#f8f3ec]'
                    : 'border border-[#e7dccd] bg-[#faf7f3] text-[#28231f]',
                ].join(' ')}
              >
                {message.text}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-[24px] border border-[#d9d0c5] bg-[#faf7f3] p-3">
          <div className="flex items-center gap-3">
            <input
              aria-label="Ask a question"
              className="flex-1 bg-transparent text-sm text-[#171513] outline-none placeholder:text-[#72685c]"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask a question about the corpus"
            />
            <button onClick={() => handleSend()} disabled={isSending} className="rounded-full bg-[#171513] px-4 py-2 text-sm font-medium text-[#f7f3ee] disabled:opacity-70">
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
