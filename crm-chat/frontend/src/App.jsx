import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage() {
    const text = input.trim()
    if (!text || loading) return

    const userMessage = { role: 'user', content: text }
    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      setMessages([...nextMessages, { role: 'assistant', content: data.response }])
    } catch (err) {
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: `**Error:** ${err.message}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  function copyChat() {
    const text = messages
      .map((m) => `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`)
      .join('\n\n')
    navigator.clipboard.writeText(text)
  }

  function newChat() {
    setMessages([])
    setInput('')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>CRM Chat</h1>
        <div className="header-actions">
          {messages.length > 0 && (
            <button onClick={copyChat} className="btn btn-secondary">
              Copy
            </button>
          )}
          <button onClick={newChat} className="btn btn-secondary">
            New Chat
          </button>
        </div>
      </header>

      <div className="messages">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            Ask anything about your CRM data…
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="bubble">
              {msg.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="bubble loading">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your CRM… (Enter to send, Shift+Enter for newline)"
          rows={2}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn btn-primary">
          Send
        </button>
      </div>
    </div>
  )
}
