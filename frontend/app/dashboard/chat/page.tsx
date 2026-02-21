'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const msgs = [...messages, userMsg].map((m) => ({ role: m.role, content: m.content }));
      const res = await api.post<{ message: string }>('/chatbot/', { messages: msgs });
      setMessages((m) => [...m, { role: 'assistant', content: res.data.message }]);
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: 'Sorry, I could not respond.' }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <h1 className="text-2xl font-bold mb-4">AI Career Mentor</h1>
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 rounded-lg bg-slate-800/30 border border-slate-700">
        {messages.length === 0 ? (
          <p className="text-slate-400">Ask about skill gaps, career paths, or job readiness.</p>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
              <div
                className={
                  m.role === 'user'
                    ? 'inline-block px-4 py-2 rounded-lg bg-cyan-600/50 text-cyan-100'
                    : 'inline-block px-4 py-2 rounded-lg bg-slate-700 text-slate-200'
                }
              >
                {m.content}
              </div>
            </div>
          ))
        )}
        {loading && <p className="text-slate-400">Thinking...</p>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
          className="flex-1 px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium"
        >
          Send
        </button>
      </form>
    </div>
  );
}
