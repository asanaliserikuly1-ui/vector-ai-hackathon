'use client'

import React, { useMemo, useState } from 'react'
import { MessageCircle, Send, Mail, Phone, Search, Heart } from 'lucide-react'

type Post = {
  id: string
  author: string
  role?: string
  title: string
  text: string
  createdAt: string
  likes: number
}

function uid() {
  return Math.random().toString(36).slice(2, 10)
}

export default function CommunityPage() {
  // --- Forum state (local demo) ---
  const [query, setQuery] = useState('')
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const [posts, setPosts] = useState<Post[]>([
    {
      id: 'p1',
      author: 'VECTOR AI',
      role: 'Команда',
      title: 'Добро пожаловать!',
      text: 'Здесь вы можете задавать вопросы, делиться опытом и писать в поддержку — всё в одном месте.',
      createdAt: new Date().toLocaleString(),
      likes: 12,
    },
  ])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return posts
    return posts.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.text.toLowerCase().includes(q) ||
        p.author.toLowerCase().includes(q)
    )
  }, [posts, query])

  function addPost() {
    const t = title.trim()
    const b = text.trim()
    if (!t || !b) return
    setPosts((prev) => [
      {
        id: uid(),
        author: 'Пользователь',
        role: 'Студент',
        title: t,
        text: b,
        createdAt: new Date().toLocaleString(),
        likes: 0,
      },
      ...prev,
    ])
    setTitle('')
    setText('')
  }

  function like(id: string) {
    setPosts((prev) =>
      prev.map((p) => (p.id === id ? { ...p, likes: p.likes + 1 } : p))
    )
  }

  // --- Support form state ---
  const [supportTopic, setSupportTopic] = useState('Подписка / доступ')
  const [supportMsg, setSupportMsg] = useState('')
  const [supportEmail, setSupportEmail] = useState('')

  function sendSupport() {
    // Тут можно потом подключить реальный API.
    // Сейчас просто показываем “успешно”.
    const msg = supportMsg.trim()
    if (!msg) return
    alert('Сообщение отправлено в поддержку ✅')
    setSupportMsg('')
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-xl bg-orange-100 text-orange-600">
          <MessageCircle className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Форум и поддержка</h1>
          <p className="text-slate-500">
            Вопросы, обсуждения и связь с командой — в одном месте.
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 mb-6">
        <div className="flex items-center gap-2 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            className="w-full outline-none text-slate-800"
            placeholder="Поиск по обсуждениям…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Forum колонка */}
        <div className="lg:col-span-2 space-y-6">
          {/* New post */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <MessageCircle className="w-4 h-4 text-orange-600" />
              <h2 className="font-semibold">Создать обсуждение</h2>
            </div>

            <input
              className="w-full rounded-xl border border-slate-200 px-3 py-2 mb-3 outline-none focus:ring-2 focus:ring-orange-200"
              placeholder="Заголовок…"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />

            <textarea
              className="w-full min-h-[110px] rounded-xl border border-slate-200 px-3 py-2 outline-none focus:ring-2 focus:ring-orange-200"
              placeholder="Текст сообщения…"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />

            <div className="flex justify-end mt-3">
              <button
                onClick={addPost}
                className="inline-flex items-center gap-2 rounded-xl bg-orange-600 text-white px-4 py-2 hover:bg-orange-700 transition"
              >
                <Send className="w-4 h-4" />
                Опубликовать
              </button>
            </div>
          </div>

          {/* Posts */}
          <div className="space-y-4">
            {filtered.map((p) => (
              <div
                key={p.id}
                className="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <div className="font-semibold">{p.title}</div>
                      {p.role ? (
                        <span className="text-xs px-2 py-1 rounded-full bg-orange-100 text-orange-700">
                          {p.role}
                        </span>
                      ) : null}
                    </div>
                    <div className="text-sm text-slate-500 mt-1">
                      {p.author} • {p.createdAt}
                    </div>
                  </div>

                  <button
                    onClick={() => like(p.id)}
                    className="inline-flex items-center gap-1 text-slate-600 hover:text-orange-700"
                    title="Нравится"
                  >
                    <Heart className="w-4 h-4" />
                    <span className="text-sm">{p.likes}</span>
                  </button>
                </div>

                <div className="text-slate-800 mt-3 whitespace-pre-wrap">
                  {p.text}
                </div>
              </div>
            ))}

            {filtered.length === 0 ? (
              <div className="text-slate-500">Ничего не найдено.</div>
            ) : null}
          </div>
        </div>

        {/* Support колонка */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 mb-3">
              <Mail className="w-4 h-4 text-orange-600" />
              <h2 className="font-semibold">Связь с поддержкой</h2>
            </div>

            <label className="block text-sm text-slate-600 mb-1">Email</label>
            <input
              className="w-full rounded-xl border border-slate-200 px-3 py-2 mb-3 outline-none focus:ring-2 focus:ring-orange-200"
              placeholder="you@example.com"
              value={supportEmail}
              onChange={(e) => setSupportEmail(e.target.value)}
            />

            <label className="block text-sm text-slate-600 mb-1">Тема</label>
            <select
              className="w-full rounded-xl border border-slate-200 px-3 py-2 mb-3 outline-none focus:ring-2 focus:ring-orange-200 bg-white"
              value={supportTopic}
              onChange={(e) => setSupportTopic(e.target.value)}
            >
              <option>Подписка / доступ</option>
              <option>Вакансии / фильтры</option>
              <option>Профиль</option>
              <option>Другое</option>
            </select>

            <label className="block text-sm text-slate-600 mb-1">
              Сообщение
            </label>
            <textarea
              className="w-full min-h-[120px] rounded-xl border border-slate-200 px-3 py-2 outline-none focus:ring-2 focus:ring-orange-200"
              placeholder="Опишите проблему…"
              value={supportMsg}
              onChange={(e) => setSupportMsg(e.target.value)}
            />

            <button
              onClick={sendSupport}
              className="w-full mt-3 inline-flex items-center justify-center gap-2 rounded-xl bg-orange-600 text-white px-4 py-2 hover:bg-orange-700 transition"
            >
              <Send className="w-4 h-4" />
              Отправить
            </button>

            <div className="mt-4 text-sm text-slate-500 space-y-2">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4" />
                <span>+7 (___) ___-__-__</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                <span>support@vector.ai</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-orange-50 p-4">
            <div className="font-semibold mb-1">Подсказка</div>
            <div className="text-sm text-slate-600">
              Чтобы быстрее помочь, укажи: страницу, что нажал(а), и что ожидал(а)
              увидеть.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}