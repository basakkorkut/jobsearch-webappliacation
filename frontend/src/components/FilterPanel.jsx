const WORK_PREFS = [
  { value: 'remote',  label: 'Uzaktan' },
  { value: 'hybrid',  label: 'Hibrit' },
  { value: 'on_site', label: 'Ofis' },
]

export default function FilterPanel({ filters, onChange }) {
  const toggle = (key, value) => {
    const current = filters[key] || []
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value]
    onChange({ ...filters, [key]: next })
  }

  const setField = (key, value) => onChange({ ...filters, [key]: value })

  const activeCount = Object.values(filters).flat().filter(Boolean).length

  return (
    <aside className="bg-white rounded-xl border border-gray-200 p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-gray-800 text-sm">Filtreler</h2>
        {activeCount > 0 && (
          <button
            onClick={() => onChange({})}
            className="text-xs text-primary-600 hover:underline"
          >
            Temizle ({activeCount})
          </button>
        )}
      </div>

      {/* Çalışma şekli */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Çalışma Şekli</p>
        {WORK_PREFS.map(({ value, label }) => (
          <label key={value} className="flex items-center gap-2 py-1 cursor-pointer">
            <input
              type="checkbox"
              className="accent-primary-600"
              checked={(filters.working_preference || []).includes(value)}
              onChange={() => toggle('working_preference', value)}
            />
            <span className="text-sm text-gray-700">{label}</span>
          </label>
        ))}
      </div>

      {/* Ülke */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Ülke</p>
        <input
          type="text"
          placeholder="Ülke adı"
          value={filters.country || ''}
          onChange={(e) => setField('country', e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      {/* Şehir */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Şehir</p>
        <input
          type="text"
          placeholder="Şehir adı"
          value={filters.city || ''}
          onChange={(e) => setField('city', e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      {/* İlçe */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">İlçe</p>
        <input
          type="text"
          placeholder="İlçe adı"
          value={filters.town || ''}
          onChange={(e) => setField('town', e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>
    </aside>
  )
}
