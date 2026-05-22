import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const EMPTY_FORM = {
  company_id: '', title: '', description: '',
  country: 'Turkey', city: '', town: '',
  working_preference: 'hybrid', position_level: 'mid',
  department: '', employment_type: 'full_time',
}

export default function Admin() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [jobs, setJobs]       = useState([])
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editJob, setEditJob]   = useState(null)
  const [form, setForm]         = useState(EMPTY_FORM)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState('')
  const [page, setPage]         = useState(1)
  const [total, setTotal]       = useState(0)

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    api.get('/api/v1/companies?limit=100').then((r) => setCompanies(r.items || [])).catch(() => {})
    fetchJobs(1)
  }, [user])

  const fetchJobs = (p) => {
    setLoading(true)
    api.get(`/api/v1/jobs?page=${p}&limit=10`)
      .then((r) => { setJobs(r.items || []); setTotal(r.total || 0); setPage(p) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const openCreate = () => { setEditJob(null); setForm(EMPTY_FORM); setError(''); setShowForm(true) }
  const openEdit   = (job) => {
    setEditJob(job)
    setForm({
      company_id:         job.company_id,
      title:              job.title,
      description:        job.description,
      country:            job.country,
      city:               job.city,
      town:               job.town || '',
      working_preference: job.working_preference || 'hybrid',
      position_level:     job.position_level || 'mid',
      department:         job.department || '',
      employment_type:    job.employment_type || 'full_time',
    })
    setError('')
    setShowForm(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (editJob) {
        const updated = await api.put(`/api/v1/jobs/${editJob.id}`, form)
        setJobs((j) => j.map((x) => x.id === editJob.id ? updated : x))
      } else {
        const created = await api.post('/api/v1/jobs', form)
        setJobs((j) => [created, ...j])
        setTotal((t) => t + 1)
      }
      setShowForm(false)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Bu ilanı silmek istediğine emin misin?')) return
    await api.delete(`/api/v1/jobs/${id}`)
    setJobs((j) => j.filter((x) => x.id !== id))
    setTotal((t) => t - 1)
  }

  const SELECT_CLASSES = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">İlan Yönetimi</h1>
        <button onClick={openCreate} className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 transition">
          + Yeni İlan
        </button>
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 overflow-auto py-8">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl mx-4 p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold">{editJob ? 'İlanı Düzenle' : 'Yeni İlan Oluştur'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Şirket *</label>
                  <select value={form.company_id} onChange={(e) => set('company_id', e.target.value)} required className={SELECT_CLASSES}>
                    <option value="">Şirket seç</option>
                    {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Başlık *</label>
                  <input type="text" required value={form.title} onChange={(e) => set('title', e.target.value)}
                    className={SELECT_CLASSES} placeholder="Senior Backend Engineer" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama *</label>
                  <textarea required rows={4} value={form.description} onChange={(e) => set('description', e.target.value)}
                    className={SELECT_CLASSES} placeholder="İlan açıklaması..." />
                </div>
                {[
                  { k: 'country', label: 'Ülke', placeholder: 'Turkey' },
                  { k: 'city',    label: 'Şehir', placeholder: 'Istanbul' },
                  { k: 'town',    label: 'İlçe',  placeholder: 'Kadıköy' },
                  { k: 'department', label: 'Departman', placeholder: 'Engineering' },
                ].map(({ k, label, placeholder }) => (
                  <div key={k}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                    <input type="text" value={form[k]} onChange={(e) => set(k, e.target.value)}
                      className={SELECT_CLASSES} placeholder={placeholder} />
                  </div>
                ))}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Çalışma Şekli</label>
                  <select value={form.working_preference} onChange={(e) => set('working_preference', e.target.value)} className={SELECT_CLASSES}>
                    <option value="hybrid">Hibrit</option>
                    <option value="remote">Uzaktan</option>
                    <option value="on_site">Ofis</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Seviye</label>
                  <select value={form.position_level} onChange={(e) => set('position_level', e.target.value)} className={SELECT_CLASSES}>
                    {['intern','junior','mid','senior','expert'].map((v) => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">İstihdam Türü</label>
                  <select value={form.employment_type} onChange={(e) => set('employment_type', e.target.value)} className={SELECT_CLASSES}>
                    <option value="full_time">Tam Zamanlı</option>
                    <option value="part_time">Yarı Zamanlı</option>
                    <option value="contract">Sözleşmeli</option>
                    <option value="internship">Staj</option>
                  </select>
                </div>
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="flex-1 border border-gray-300 text-gray-700 py-2 rounded-lg text-sm font-medium hover:bg-gray-50">İptal</button>
                <button type="submit" disabled={saving} className="flex-1 bg-primary-600 text-white py-2 rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50">
                  {saving ? 'Kaydediliyor...' : editJob ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Job list */}
      {loading ? (
        <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="bg-white rounded-xl border p-5 animate-pulse h-20" />)}</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">📋</p>
          <p className="font-medium">Henüz ilan yok</p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {jobs.map((job) => (
              <div key={job.id} className="bg-white rounded-xl border border-gray-200 p-5 flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{job.title}</p>
                  <p className="text-sm text-gray-500">{job.company?.name} · {job.city} · {job.application_count} başvuru</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => openEdit(job)} className="text-sm text-blue-600 hover:underline">Düzenle</button>
                  <button onClick={() => handleDelete(job.id)} className="text-sm text-red-400 hover:text-red-600">Sil</button>
                </div>
              </div>
            ))}
          </div>
          {total > 10 && (
            <div className="flex justify-center gap-2 mt-6">
              {[...Array(Math.ceil(total / 10))].map((_, i) => (
                <button key={i} onClick={() => fetchJobs(i + 1)}
                  className={`w-9 h-9 rounded-lg text-sm ${page === i + 1 ? 'bg-primary-600 text-white' : 'bg-white border border-gray-300 text-gray-600 hover:border-primary-400'}`}>
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
