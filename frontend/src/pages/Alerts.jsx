import { useEffect, useState } from 'react'
import JobAlertModal from '../components/JobAlertModal'
import { api } from '../lib/api'

export default function Alerts() {
  const [alerts, setAlerts]   = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    api.get('/api/v1/alerts').then(setAlerts).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id) => {
    await api.delete(`/api/v1/alerts/${id}`)
    setAlerts((a) => a.filter((x) => x.id !== id))
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">İş Alarmlarım</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 transition"
        >
          + Alarm Ekle
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse h-20" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🔔</p>
          <p className="font-medium">Henüz alarm yok</p>
          <p className="text-sm mt-1">İş alarmı oluşturarak yeni ilanlardan haberdar ol</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between">
              <div>
                <p className="font-semibold text-gray-900">{a.keywords}</p>
                <p className="text-sm text-gray-500 mt-0.5">
                  {[a.city, a.country].filter(Boolean).join(', ') || 'Tüm konumlar'}
                </p>
              </div>
              <button
                onClick={() => handleDelete(a.id)}
                className="text-red-400 hover:text-red-600 text-sm font-medium transition"
              >
                Sil
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <JobAlertModal
          onClose={() => setShowModal(false)}
          onCreated={(a) => setAlerts((prev) => [a, ...prev])}
        />
      )}
    </div>
  )
}
