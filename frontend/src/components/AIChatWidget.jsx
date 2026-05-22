import { useState, useRef, useEffect } from 'react'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../lib/supabase'

export default function AIChatWidget() {
  const { user } = useAuth()
  const [open, setOpen]       = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Merhaba! İş arama konusunda sana yardımcı olabilirim. Ne arıyorsun?' }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      const payload = {
        messages: [...messages, userMsg],
        user_jwt: session?.access_token || null,
      }
      const res = await api.post('/api/v1/agent/chat', payload)
      setMessages((m) => [...m, { role: 'assistant', content: res.response }])
    } catch {
      setMessages((m) => [...m, {
        role: 'assistant',
        content: 'AI Agent şu an çevrimdışı. Lütfen daha sonra tekrar dene.'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-40 bg-primary-600 text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-2xl hover:bg-primary-700 transition"
        title="AI Asistan"
      >
        {open ? '✕' : '🤖'}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-80 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          <div className="bg-primary-600 text-white px-4 py-3 flex items-center gap-2">
            <span className="text-lg">🤖</span>
            <span className="font-semibold text-sm">AI İş Asistanı</span>
          </div>

          <div className="flex-1 overflow-auto p-3 space-y-2 max-h-72">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 px-3 py-2 rounded-xl text-sm text-gray-500 animate-pulse">Yazıyor...</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="border-t border-gray-200 p-3 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder={user ? "Mesajını yaz..." : "Giriş yaparak kullan"}
              disabled={!user || loading}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 disabled:bg-gray-50"
            />
            <button
              onClick={send}
              disabled={!user || loading || !input.trim()}
              className="bg-primary-600 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition disabled:opacity-40"
            >
              Gönder
            </button>
          </div>
        </div>
      )}
    </>
  )
}
