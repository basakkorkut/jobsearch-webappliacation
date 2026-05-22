import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signUp } = useAuth()
  const navigate   = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'candidate' })
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) { setError('Şifre en az 6 karakter olmalı'); return }
    setLoading(true)
    const { error: err } = await signUp(form.email, form.password, {
      full_name: form.full_name,
      role: form.role,
    })
    setLoading(false)
    if (err) { setError(err.message); return }
    navigate('/login', { state: { message: 'Kayıt başarılı! E-postanı onayla ve giriş yap.' } })
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-sm p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Kayıt Ol</h1>
        <p className="text-sm text-gray-500 mb-6">Ücretsiz hesap oluştur</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ad Soyad</label>
            <input type="text" required value={form.full_name}
              onChange={(e) => set('full_name', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-primary-500"
              placeholder="Ad Soyad"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">E-posta</label>
            <input type="email" required value={form.email}
              onChange={(e) => set('email', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-primary-500"
              placeholder="ornek@mail.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Şifre</label>
            <input type="password" required value={form.password}
              onChange={(e) => set('password', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-primary-500"
              placeholder="••••••••"
            />
          </div>

          {/* Role selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Hesap Türü</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'candidate', label: '👤 Aday',    desc: 'İş arıyorum' },
                { value: 'company',   label: '🏢 Şirket',  desc: 'İlan yayınlıyorum' },
              ].map(({ value, label, desc }) => (
                <label
                  key={value}
                  className={`cursor-pointer border-2 rounded-xl p-3 text-center transition ${
                    form.role === value
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input type="radio" name="role" value={value} className="sr-only"
                    checked={form.role === value} onChange={() => set('role', value)} />
                  <p className="font-medium text-sm text-gray-900">{label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                </label>
              ))}
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full bg-primary-600 text-white py-2.5 rounded-lg font-semibold text-sm hover:bg-primary-700 transition disabled:opacity-50">
            {loading ? 'Kaydediliyor...' : 'Kayıt Ol'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-5">
          Zaten hesabın var mı?{' '}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">Giriş yap</Link>
        </p>
      </div>
    </div>
  )
}
