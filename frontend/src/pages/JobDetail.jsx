import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import JobCard from '../components/JobCard'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function JobDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [job, setJob]       = useState(null)
  const [related, setRelated] = useState([])
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [applied, setApplied]   = useState(false)
  const [error, setError]       = useState('')

  useEffect(() => {
    setLoading(true)
    setApplied(false)
    setError('')
    Promise.all([
      api.get(`/api/v1/jobs/${id}`),
      api.get(`/api/v1/jobs/${id}/related`),
    ])
      .then(([j, r]) => { setJob(j); setRelated(r) })
      .catch(() => setError('İlan bulunamadı'))
      .finally(() => setLoading(false))
  }, [id])

  const handleApply = async () => {
    if (!user) { navigate('/login', { state: { from: `/jobs/${id}` } }); return }
    setApplying(true)
    try {
      await api.post(`/api/v1/jobs/${id}/apply`)
      setApplied(true)
      setJob((j) => ({ ...j, application_count: j.application_count + 1 }))
    } catch (err) {
      setError(err.message)
    } finally {
      setApplying(false)
    }
  }

  if (loading) return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/2" />
        <div className="h-4 bg-gray-200 rounded w-1/4" />
        <div className="h-40 bg-gray-200 rounded" />
      </div>
    </div>
  )

  if (error && !job) return (
    <div className="max-w-7xl mx-auto px-4 py-16 text-center text-gray-400">
      <p className="text-4xl mb-3">😕</p>
      <p className="font-medium">{error}</p>
      <Link to="/search" className="text-primary-600 text-sm mt-2 inline-block hover:underline">← İlanlara dön</Link>
    </div>
  )

  const PREF = { remote: 'Uzaktan', on_site: 'Ofis', hybrid: 'Hibrit' }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <Link to="/search" className="text-sm text-primary-600 hover:underline mb-6 inline-block">← İlanlara dön</Link>

      <div className="flex gap-8 flex-col lg:flex-row">
        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-2xl border border-gray-200 p-7">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{job.title}</h1>
                <p className="text-primary-600 font-medium mt-1">{job.company?.name}</p>
              </div>
              {applied ? (
                <span className="bg-green-100 text-green-700 px-4 py-2 rounded-lg text-sm font-semibold shrink-0">✓ Başvuruldu</span>
              ) : user ? (
                <button
                  onClick={handleApply}
                  disabled={applying}
                  className="bg-primary-600 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-primary-700 transition disabled:opacity-50 shrink-0"
                >
                  {applying ? 'Başvuruluyor...' : 'Başvur'}
                </button>
              ) : (
                <Link
                  to="/login"
                  state={{ from: `/jobs/${id}` }}
                  className="bg-primary-600 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-primary-700 transition shrink-0"
                >
                  Giriş yap & Başvur
                </Link>
              )}
            </div>

            {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

            {/* Meta badges */}
            <div className="flex flex-wrap gap-2 mb-6">
              <span className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full">
                📍 {job.city}{job.town ? `, ${job.town}` : ''}, {job.country}
              </span>
              {job.working_preference && (
                <span className="text-xs bg-primary-100 text-primary-700 px-3 py-1.5 rounded-full">
                  {PREF[job.working_preference] || job.working_preference}
                </span>
              )}
              {job.position_level && (
                <span className="text-xs bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full">
                  {job.position_level}
                </span>
              )}
              {job.employment_type && (
                <span className="text-xs bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full">
                  {job.employment_type.replace('_', ' ')}
                </span>
              )}
              {job.department && (
                <span className="text-xs bg-blue-100 text-blue-700 px-3 py-1.5 rounded-full">
                  {job.department}
                </span>
              )}
            </div>

            <div className="flex gap-4 text-sm text-gray-400 border-t border-gray-100 pt-4 mb-6">
              <span>{job.application_count} başvuru</span>
              <span>·</span>
              <span>Güncellendi: {new Date(job.updated_at).toLocaleDateString('tr-TR')}</span>
            </div>

            {/* Description */}
            <div className="prose max-w-none text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
              {job.description}
            </div>
          </div>
        </div>

        {/* Related jobs */}
        {related.length > 0 && (
          <aside className="lg:w-72 shrink-0">
            <h2 className="font-semibold text-gray-800 mb-4">Benzer İlanlar</h2>
            <div className="space-y-3">
              {related.map((r) => <JobCard key={r.id} job={r} />)}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
