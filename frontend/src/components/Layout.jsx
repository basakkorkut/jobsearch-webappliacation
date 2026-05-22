import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold tracking-tight hover:opacity-90">
            JobSearch
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link to="/" className="hover:text-primary-200 transition">Ana Sayfa</Link>
            <Link to="/search" className="hover:text-primary-200 transition">İlanlar</Link>
            {user && (
              <>
                <Link to="/alerts" className="hover:text-primary-200 transition">Alarmlarım</Link>
                <Link to="/notifications" className="hover:text-primary-200 transition">Bildirimler</Link>
                <Link to="/admin" className="hover:text-primary-200 transition">Panelim</Link>
              </>
            )}
          </nav>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <span className="text-sm text-primary-200 hidden md:block truncate max-w-[160px]">
                  {user.email}
                </span>
                <button
                  onClick={handleSignOut}
                  className="text-sm bg-white text-primary-700 px-3 py-1.5 rounded-md font-semibold hover:bg-primary-100 transition"
                >
                  Çıkış
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm hover:text-primary-200 transition">Giriş</Link>
                <Link
                  to="/signup"
                  className="text-sm bg-white text-primary-700 px-3 py-1.5 rounded-md font-semibold hover:bg-primary-100 transition"
                >
                  Kayıt Ol
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-gray-400 text-sm py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 text-center">
          © 2025 JobSearch · SE4458 Final Project
        </div>
      </footer>
    </div>
  )
}
