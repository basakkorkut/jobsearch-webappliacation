import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

function AutocompleteInput({ placeholder, value, onChange, fetchSuggestions, icon }) {
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const debounced = useDebounce(value, 300)
  const ref = useRef(null)

  useEffect(() => {
    if (debounced.length < 1) { setSuggestions([]); return }
    fetchSuggestions(debounced).then(setSuggestions).catch(() => setSuggestions([]))
  }, [debounced])

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="relative flex-1" ref={ref}>
      <div className="flex items-center bg-white border border-gray-300 rounded-lg px-3 py-2.5 focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500">
        <span className="mr-2 text-gray-400">{icon}</span>
        <input
          type="text"
          className="flex-1 outline-none text-sm text-gray-700 placeholder-gray-400 bg-transparent"
          placeholder={placeholder}
          value={value}
          onChange={(e) => { onChange(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
        />
      </div>
      {open && suggestions.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-auto">
          {suggestions.map((s) => (
            <li
              key={s}
              className="px-4 py-2.5 text-sm text-gray-700 cursor-pointer hover:bg-primary-50 hover:text-primary-700"
              onMouseDown={() => { onChange(s); setOpen(false) }}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function SearchBar({ initialPosition = '', initialCity = '', compact = false }) {
  const [position, setPosition] = useState(initialPosition)
  const [city, setCity]         = useState(initialCity)
  const navigate = useNavigate()

  useEffect(() => { setPosition(initialPosition) }, [initialPosition])
  useEffect(() => { setCity(initialCity) }, [initialCity])

  const fetchPositions = (q) => api.get(`/api/v1/search/autocomplete/positions?q=${encodeURIComponent(q)}`)
  const fetchCities    = (q) => api.get(`/api/v1/search/autocomplete/cities?q=${encodeURIComponent(q)}`)

  const handleSearch = (e) => {
    e.preventDefault()
    const params = new URLSearchParams()
    if (position) params.set('position', position)
    if (city)     params.set('city', city)
    navigate(`/search?${params.toString()}`)
  }

  return (
    <form onSubmit={handleSearch} className={`flex flex-col sm:flex-row gap-3 ${compact ? '' : 'w-full max-w-3xl'}`}>
      <AutocompleteInput
        placeholder="Pozisyon veya anahtar kelime"
        value={position}
        onChange={setPosition}
        fetchSuggestions={fetchPositions}
        icon="💼"
      />
      <AutocompleteInput
        placeholder="Şehir"
        value={city}
        onChange={setCity}
        fetchSuggestions={fetchCities}
        icon="📍"
      />
      <button
        type="submit"
        className="bg-primary-600 text-white px-6 py-2.5 rounded-lg font-semibold text-sm hover:bg-primary-700 transition whitespace-nowrap"
      >
        İş Ara
      </button>
    </form>
  )
}
