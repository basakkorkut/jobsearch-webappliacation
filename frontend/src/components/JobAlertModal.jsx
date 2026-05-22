import { useState } from 'react'
import { api } from '../lib/api'

export default function JobAlertModal({ onClose, onCreated }) {
  const [form, setForm]     = useState({ keywords: '', country: '', city: '', town: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.keywords.trim()) { setError('Anahtar kelime zorunlu'); return }
    setLoading(true)
    try {
      const alert = await api.post('/api/v1/alerts', {
        keywords: form.keywords,
        country:  form.country  || null,
        city:     form.city     || null,
        town:     form.town     || null,
      })
      onCreated(alert)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900">İş Alarmı Oluştur</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { key: 'keywords', label: 'Anahtar Kelimeler *', placeholder: 'React, Python, DevOps...' },
            { key: 'country',  label: 'Ülke',                placeholder: 'Turkey' },
            { key: 'city',     label: 'Şehir',               placeholder: 'Istanbul' },
            { key: 'town',     label: 'İlçe',                placeholder: 'Kadıköy' },
          ].map(({ key, label, placeholder }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type="text"
                placeholder={placeholder}
                value={form[key]}
                onChange={(e) => set(key, e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              />
            </div>
          ))}

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition">
              İptal
            </button>
            <button type="submit" disabled={loading} className="flex-1 bg-primary-600 text-white py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 transition disabled:opacity-50">
              {loading ? 'Kaydediliyor...' : 'Alarm Oluştur'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
