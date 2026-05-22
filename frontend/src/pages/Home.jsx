import { useEffect, useState } from 'react'
import SearchBar from '../components/SearchBar'
import JobCard from '../components/JobCard'
import AIChatWidget from '../components/AIChatWidget'
import { api } from '../lib/api'
import { getCurrentCity } from '../lib/geolocation'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()
  const [featuredJobs, setFeaturedJobs] = useState([])
  const [recentSearches, setRecentSearches] = useState([])
  const [city, setCity] = useState('')
  const [loadingFeatured, setLoadingFeatured] = useState(false)

  // Geolocation → featured jobs
  useEffect(() => {
    getCurrentCity()
      .then((c) => {
        if (!c) return
        setCity(c)
        setLoadingFeatured(true)
        return api.get(`/api/v1/search/featured?city=${encodeURIComponent(c)}`)
      })
      .then((jobs) => { if (jobs) setFeaturedJobs(jobs) })
      .catch(() => {
        // Geolocation denied or failed — load Istanbul as default
        setCity('Istanbul')
        api.get('/api/v1/search/featured?city=Istanbul')
          .then(setFeaturedJobs)
          .catch(() => {})
      })
      .finally(() => setLoadingFeatured(false))
  }, [])

  // Recent searches if logged in
  useEffect(() => {
    if (!user) return
    api.get('/api/v1/search/recent').then(setRecentSearches).catch(() => {})
  }, [user])

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
          Hayalindeki İşi Bul
        </h1>
        <p className="text-lg text-gray-500 mb-8">
          Binlerce ilan arasından sana en uygun pozisyonu keşfet
        </p>
        <div className="flex justify-center">
          <SearchBar />
        </div>
      </div>

      {/* Recent Searches */}
      {user && recentSearches.length > 0 && (
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Son Aramalarım</h2>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((s) => {
              const q = s.query || {}
              const label = [q.position, q.city].filter(Boolean).join(' · ') || 'Arama'
              const params = new URLSearchParams(Object.fromEntries(
                Object.entries(q).filter(([, v]) => v)
              ))
              return (
                <a
                  key={s.id}
                  href={`/search?${params}`}
                  className="text-sm bg-primary-50 text-primary-700 border border-primary-200 px-3 py-1.5 rounded-full hover:bg-primary-100 transition"
                >
                  🔍 {label}
                </a>
              )
            })}
          </div>
        </section>
      )}

      {/* Featured Jobs */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          {city ? `${city}'deki Güncel İlanlar` : 'Güncel İlanlar'}
        </h2>
        {loadingFeatured ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse h-32" />
            ))}
          </div>
        ) : featuredJobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featuredJobs.map((job) => <JobCard key={job.id} job={job} />)}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Bu şehirde ilan bulunamadı.</p>
        )}
      </section>

      <AIChatWidget />
    </div>
  )
}
