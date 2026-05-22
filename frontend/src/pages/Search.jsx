import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import FilterPanel from '../components/FilterPanel'
import JobCard from '../components/JobCard'
import SearchBar from '../components/SearchBar'
import { api } from '../lib/api'

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [results, setResults]   = useState({ items: [], total: 0, pages: 1 })
  const [loading, setLoading]   = useState(false)

  const position = searchParams.get('position') || ''
  const city     = searchParams.get('city')     || ''
  const page     = parseInt(searchParams.get('page') || '1')

  const [filters, setFilters] = useState({
    country:            searchParams.get('country')            || '',
    city:               city,
    town:               searchParams.get('town')               || '',
    working_preference: searchParams.getAll('working_preference'),
  })

  // Fetch on param change
  useEffect(() => {
    const params = new URLSearchParams(searchParams)
    const path = `/api/v1/search?${params.toString()}&limit=12`
    setLoading(true)
    api.get(path)
      .then(setResults)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [searchParams.toString()])

  const applyFilters = (f) => {
    setFilters(f)
    const next = new URLSearchParams()
    if (position) next.set('position', position)
    if (f.city)    next.set('city', f.city)
    if (f.country) next.set('country', f.country)
    if (f.town)    next.set('town', f.town)
    ;(f.working_preference || []).forEach((v) => next.append('working_preference', v))
    next.set('page', '1')
    setSearchParams(next)
  }

  const goPage = (p) => {
    const next = new URLSearchParams(searchParams)
    next.set('page', p)
    setSearchParams(next)
    window.scrollTo(0, 0)
  }

  // Active filter chips
  const chips = [
    position && { label: `Pozisyon: ${position}`, key: 'position' },
    filters.city && { label: `Şehir: ${filters.city}`, key: 'city' },
    filters.country && { label: `Ülke: ${filters.country}`, key: 'country' },
    ...(filters.working_preference || []).map((v) => ({ label: v, key: 'wp_' + v })),
  ].filter(Boolean)

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Search bar */}
      <div className="mb-6">
        <SearchBar initialPosition={position} initialCity={filters.city} compact />
      </div>

      {/* Active filter chips */}
      {chips.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {chips.map(({ label, key }) => (
            <span key={key} className="text-xs bg-primary-100 text-primary-700 px-3 py-1 rounded-full flex items-center gap-1">
              {label}
              <button
                onClick={() => {
                  const f = { ...filters }
                  if (key === 'position') { const p = new URLSearchParams(searchParams); p.delete('position'); setSearchParams(p) }
                  else if (key === 'city') applyFilters({ ...f, city: '' })
                  else if (key === 'country') applyFilters({ ...f, country: '' })
                  else if (key.startsWith('wp_')) applyFilters({ ...f, working_preference: (f.working_preference || []).filter((v) => 'wp_' + v !== key) })
                }}
                className="ml-1 hover:text-primary-900 text-base leading-none"
              >×</button>
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-6">
        {/* Filter panel */}
        <div className="hidden md:block w-56 shrink-0">
          <FilterPanel filters={filters} onChange={applyFilters} />
        </div>

        {/* Results */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              {loading ? 'Yükleniyor...' : `${results.total} ilan bulundu`}
            </p>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse h-32" />
              ))}
            </div>
          ) : results.items.length > 0 ? (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {results.items.map((job) => <JobCard key={job.id} job={job} />)}
              </div>

              {/* Pagination */}
              {results.pages > 1 && (
                <div className="flex justify-center gap-2 mt-8">
                  {[...Array(results.pages)].map((_, i) => {
                    const p = i + 1
                    return (
                      <button
                        key={p}
                        onClick={() => goPage(p)}
                        className={`w-9 h-9 rounded-lg text-sm font-medium transition ${
                          p === page
                            ? 'bg-primary-600 text-white'
                            : 'bg-white border border-gray-300 text-gray-600 hover:border-primary-400'
                        }`}
                      >
                        {p}
                      </button>
                    )
                  })}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-16 text-gray-400">
              <p className="text-4xl mb-3">🔍</p>
              <p className="font-medium">Sonuç bulunamadı</p>
              <p className="text-sm mt-1">Farklı filtreler dene</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
