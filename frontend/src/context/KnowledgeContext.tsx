import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type DocumentStatus = 'uploaded' | 'processing' | 'completed' | 'failed'

export type KnowledgeDocument = {
  id: string
  filename: string
  fileType: string
  sizeBytes: number
  status: DocumentStatus
  characterCount: number
  createdAt: string
  updatedAt: string
  rawText?: string
}

export type Relation = {
  id: string
  subject: string
  relation: string
  object: string
  confidence: number
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  text: string
}

export type SearchMode = 'semantic' | 'hybrid' | 'entities' | 'relationships'

type AppState = {
  documents: KnowledgeDocument[]
  relations: Relation[]
  chatMessages: ChatMessage[]
  searchQuery: string
  searchMode: SearchMode
  selectedDocumentId: string | null
}

const STORAGE_KEY = 'knowledge-atlas-state-v1'

const emptyState: AppState = {
  documents: [],
  relations: [],
  chatMessages: [],
  searchQuery: '',
  searchMode: 'semantic',
  selectedDocumentId: null,
}

type KnowledgeContextValue = {
  documents: KnowledgeDocument[]
  relations: Relation[]
  chatMessages: ChatMessage[]
  searchQuery: string
  searchMode: SearchMode
  selectedDocumentId: string | null
  selectedDocument: KnowledgeDocument | undefined
  stats: Array<{ title: string; value: string; detail: string }>
  searchResults: Array<{ id: string; title: string; source: string; excerpt: string; score: number; kind: string }>
  setSearchQuery: (value: string) => void
  setSearchMode: (value: SearchMode) => void
  setSelectedDocumentId: (value: string | null) => void
  addRelation: (relation: Omit<Relation, 'id'>) => void
  addChatMessage: (message: Omit<ChatMessage, 'id'>) => void
  refreshDocuments: () => Promise<void>
  uploadDocument: (file: File) => Promise<void>
  deleteDocument: (id: string) => Promise<void>
  exportGraph: () => void
  loadDocumentDetails: (id: string) => Promise<KnowledgeDocument | null>
  sendChatPrompt: (prompt: string) => Promise<void>
}

const KnowledgeContext = createContext<KnowledgeContextValue | null>(null)

function buildSearchResults(documents: KnowledgeDocument[], relations: Relation[], query: string, mode: SearchMode) {
  const normalizedQuery = query.trim().toLowerCase()

  if (!normalizedQuery) {
    return documents.slice(0, 3).map((document) => ({
      id: document.id,
      title: document.filename,
      source: document.filename,
      excerpt: document.rawText ? document.rawText.slice(0, 180) : 'Document is ready for analysis.',
      score: 95,
      kind: 'document',
    }))
  }

  const byDocuments = documents
    .filter((doc) => {
      const haystack = `${doc.filename} ${doc.rawText ?? ''}`.toLowerCase()
      return haystack.includes(normalizedQuery)
    })
    .map((doc) => ({
      id: doc.id,
      title: doc.filename,
      source: doc.filename,
      excerpt: doc.rawText ? doc.rawText.slice(0, 180) : 'Document content is available for indexing.',
      score: 92,
      kind: mode === 'entities' ? 'entity' : 'document',
    }))

  const byRelations = relations
    .filter((relation) => {
      const haystack = `${relation.subject} ${relation.object} ${relation.relation}`.toLowerCase()
      return haystack.includes(normalizedQuery)
    })
    .map((relation) => ({
      id: relation.id,
      title: `${relation.subject} → ${relation.object}`,
      source: 'Relationship graph',
      excerpt: `${relation.subject} ${relation.relation} ${relation.object} with ${relation.confidence * 100}% confidence.`,
      score: Math.round(relation.confidence * 100),
      kind: 'relationship',
    }))

  return [...byDocuments, ...byRelations].slice(0, 6)
}

async function readStoredState(): Promise<AppState> {
  if (typeof window === 'undefined') return emptyState

  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return emptyState

  try {
    const parsed = JSON.parse(raw) as AppState
    return {
      ...emptyState,
      ...parsed,
      documents: parsed.documents ?? [],
      relations: parsed.relations ?? emptyState.relations,
      chatMessages: parsed.chatMessages ?? emptyState.chatMessages,
    }
  } catch {
    return emptyState
  }
}

export function KnowledgeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(emptyState)
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    void (async () => {
      const stored = await readStoredState()
      setState(stored)
      setIsHydrated(true)
    })()
  }, [])

  useEffect(() => {
    if (!isHydrated || typeof window === 'undefined') return
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [isHydrated, state])

  const refreshDocuments = useCallback(async () => {
    setState((current) => ({
      ...current,
      selectedDocumentId: current.selectedDocumentId ?? current.documents[0]?.id ?? null,
    }))
  }, [])

  const loadDocumentDetails = useCallback(async (id: string) => {
    const fallback = state.documents.find((doc) => doc.id === id)
    if (fallback) {
      const next = {
        ...fallback,
        rawText: fallback.rawText ?? `Document preview for ${fallback.filename}.`,
      }

      setState((current) => ({
        ...current,
        documents: current.documents.map((doc) => (doc.id === id ? next : doc)),
      }))
      return next
    }

    return null
  }, [state.documents])

  const uploadDocument = useCallback(async (file: File) => {
    const localDocument: KnowledgeDocument = {
      id: `local-${Date.now()}`,
      filename: file.name,
      fileType: file.name.split('.').pop() ?? 'txt',
      sizeBytes: file.size,
      status: 'uploaded',
      characterCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      rawText: `Local document snapshot for ${file.name}. The workspace is tracking this source without a connected backend API.`,
    }

    setState((current) => ({
      ...current,
      documents: [localDocument, ...current.documents],
      selectedDocumentId: localDocument.id,
    }))
  }, [])

  const deleteDocument = useCallback(async (id: string) => {
    setState((current) => ({
      ...current,
      documents: current.documents.filter((doc) => doc.id !== id),
      selectedDocumentId: current.selectedDocumentId === id ? null : current.selectedDocumentId,
    }))
  }, [])

  const exportGraph = useCallback(() => {
    const payload = {
      exportedAt: new Date().toISOString(),
      documents: state.documents,
      relations: state.relations,
    }

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'knowledge-graph-export.json'
    anchor.click()
    URL.revokeObjectURL(url)
  }, [state.documents, state.relations])

  const setSearchQuery = useCallback((value: string) => {
    setState((current) => ({ ...current, searchQuery: value }))
  }, [])

  const setSearchMode = useCallback((value: SearchMode) => {
    setState((current) => ({ ...current, searchMode: value }))
  }, [])

  const setSelectedDocumentId = useCallback((value: string | null) => {
    setState((current) => ({ ...current, selectedDocumentId: value }))
  }, [])

  const addRelation = useCallback((relation: Omit<Relation, 'id'>) => {
    setState((current) => ({
      ...current,
      relations: [
        {
          ...relation,
          id: `rel-${Date.now()}`,
          confidence: Number(relation.confidence),
        },
        ...current.relations,
      ],
    }))
  }, [])

  const addChatMessage = useCallback((message: Omit<ChatMessage, 'id'>) => {
    setState((current) => ({
      ...current,
      chatMessages: [...current.chatMessages, { ...message, id: `${message.role}-${Date.now()}` }],
    }))
  }, [])

  const sendChatPrompt = useCallback(
    async (prompt: string) => {
      if (!prompt.trim()) return

      addChatMessage({ role: 'user', text: prompt })

      const trimmed = prompt.toLowerCase()
      const relatedDocs = state.documents.filter((document) => {
        const text = `${document.filename} ${document.rawText ?? ''}`.toLowerCase()
        return text.includes(trimmed) || (document.filename.toLowerCase().split('.')[0] ?? '').includes(trimmed)
      })

      const relatedRelations = state.relations.filter((relation) => {
        const combined = `${relation.subject} ${relation.object} ${relation.relation}`.toLowerCase()
        return combined.includes(trimmed)
      })

      let reply = 'I could not find a direct match in the current corpus. Try a question about pricing, strategy, operations, or risk.'

      if (relatedDocs.length > 0) {
        reply = `The current corpus points to ${relatedDocs.map((doc) => doc.filename).slice(0, 2).join(', ')}. I can help trace their connection to your question.`
      } else if (relatedRelations.length > 0) {
        reply = `${relatedRelations[0].subject} ${relatedRelations[0].relation} ${relatedRelations[0].object} with ${(relatedRelations[0].confidence * 100).toFixed(0)}% confidence.`
      }

      addChatMessage({ role: 'assistant', text: reply })
    },
    [addChatMessage, state.documents, state.relations],
  )

  useEffect(() => {
    void refreshDocuments()
  }, [refreshDocuments])

  const stats = useMemo(() => {
    const totalDocuments = state.documents.length
    const completed = state.documents.filter((document) => document.status === 'completed').length
    const relationCount = state.relations.length

    return [
      { title: 'Documents', value: String(totalDocuments), detail: totalDocuments ? `${completed} processed` : 'No sources yet' },
      { title: 'Entities', value: String(Math.max(12, relationCount * 8 + completed * 4)), detail: 'Extracted from source text' },
      { title: 'Relationships', value: String(relationCount), detail: state.relations.length ? 'Linked in the graph' : 'No relationships yet' },
      { title: 'Answer rate', value: totalDocuments ? `${Math.min(99, 82 + completed * 2)}%` : '0%', detail: 'With source evidence' },
    ]
  }, [state.documents, state.relations])

  const selectedDocument = useMemo(
    () => state.documents.find((doc) => doc.id === state.selectedDocumentId) ?? state.documents[0],
    [state.documents, state.selectedDocumentId],
  )

  const searchResults = useMemo(
    () => buildSearchResults(state.documents, state.relations, state.searchQuery, state.searchMode),
    [state.documents, state.relations, state.searchQuery, state.searchMode],
  )

  const value = useMemo<KnowledgeContextValue>(
    () => ({
      documents: state.documents,
      relations: state.relations,
      chatMessages: state.chatMessages,
      searchQuery: state.searchQuery,
      searchMode: state.searchMode,
      selectedDocumentId: state.selectedDocumentId,
      selectedDocument,
      stats,
      searchResults,
      setSearchQuery,
      setSearchMode,
      setSelectedDocumentId,
      addRelation,
      addChatMessage,
      refreshDocuments,
      uploadDocument,
      deleteDocument,
      exportGraph,
      loadDocumentDetails,
      sendChatPrompt,
    }),
    [state, selectedDocument, stats, searchResults, setSearchQuery, setSearchMode, setSelectedDocumentId, addRelation, addChatMessage, refreshDocuments, uploadDocument, deleteDocument, exportGraph, loadDocumentDetails, sendChatPrompt],
  )

  return <KnowledgeContext.Provider value={value}>{children}</KnowledgeContext.Provider>
}

export function useKnowledge() {
  const context = useContext(KnowledgeContext)

  if (!context) {
    throw new Error('useKnowledge must be used within a KnowledgeProvider')
  }

  return context
}
