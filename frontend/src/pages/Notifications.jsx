import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading]     = useState(true)
  const [readFilter, setReadFilter] = useState(null) // null=all, true=read, false=unread

  const fetchNotifications = (read) => {
    const q = read !== null ? `?read=${read}` : ''
    setLoading(true)
    api.get(`/api/v1/notifications${q}`)
      .then((res) => setNotifications(res.items || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchNotifications(readFilter) }, [readFilter])

  const markRead = async (id) => {
    await api.patch(`/api/v1/notifications/${id}/read`)
    setNotifications((n) => n.map((x) => x.id === id ? { ...x, read: true } : x))
  }

  const FILTER_OPTS = [
    { label: 'Tümü',    value: null },
    { label: 'Okunmamış', value: false },
    { label: 'Okunmuş',   value: true },
  ]

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Bildirimler</h1>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-5">
        {FILTER_OPTS.map(({ label, value }) => (
          <button
            key={String(value)}
            onClick={() => setReadFilter(value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
              readFilter === value
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border p-5 animate-pulse h-20" />
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🔕</p>
          <p className="font-medium">Bildirim yok</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`bg-white rounded-xl border p-5 flex items-start justify-between gap-4 transition ${
                n.read ? 'border-gray-200 opacity-70' : 'border-primary-200 shadow-sm'
              }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    n.type === 'job_alert' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {n.type === 'job_alert' ? '🔔 Alarm' : '🔍 Arama'}
                  </span>
                  {!n.read && (
                    <span className="w-2 h-2 bg-primary-600 rounded-full" />
                  )}
                </div>
                <p className="font-medium text-gray-900 text-sm">{n.job_posting_title}</p>
                <p className="text-xs text-gray-500 mt-0.5">{n.message}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(n.created_at).toLocaleString('tr-TR')}
                </p>
              </div>
              {!n.read && (
                <button
                  onClick={() => markRead(n.id)}
                  className="text-xs text-primary-600 hover:underline shrink-0"
                >
                  Okundu işaretle
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
