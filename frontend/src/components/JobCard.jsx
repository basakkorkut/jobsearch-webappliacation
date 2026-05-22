import { Link } from 'react-router-dom'

const PREF_LABEL = { remote: 'Uzaktan', on_site: 'Ofis', hybrid: 'Hibrit' }
const LEVEL_COLOR = {
  junior: 'bg-green-100 text-green-700',
  mid:    'bg-blue-100 text-blue-700',
  senior: 'bg-purple-100 text-purple-700',
  expert: 'bg-red-100 text-red-700',
  intern: 'bg-yellow-100 text-yellow-700',
}

export default function JobCard({ job }) {
  return (
    <Link to={`/jobs/${job.id}`} className="block">
      <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-primary-300 transition-all">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{job.company?.name}</p>
          </div>
          {job.position_level && (
            <span className={`text-xs px-2 py-1 rounded-full font-medium shrink-0 ${LEVEL_COLOR[job.position_level] || 'bg-gray-100 text-gray-600'}`}>
              {job.position_level}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
            📍 {job.city}{job.town ? `, ${job.town}` : ''}
          </span>
          {job.working_preference && (
            <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full">
              {PREF_LABEL[job.working_preference] || job.working_preference}
            </span>
          )}
          {job.employment_type && (
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
              {job.employment_type.replace('_', ' ')}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>{job.department}</span>
          <span>{job.application_count} başvuru · {new Date(job.created_at).toLocaleDateString('tr-TR')}</span>
        </div>
      </div>
    </Link>
  )
}
