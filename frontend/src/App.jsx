import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Search from './pages/Search'
import JobDetail from './pages/JobDetail'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Alerts from './pages/Alerts'
import Notifications from './pages/Notifications'
import Admin from './pages/Admin'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/"             element={<Home />} />
            <Route path="/search"       element={<Search />} />
            <Route path="/jobs/:id"     element={<JobDetail />} />
            <Route path="/login"        element={<Login />} />
            <Route path="/signup"       element={<Signup />} />
            <Route path="/alerts"       element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
            <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />
            <Route path="/admin"        element={<ProtectedRoute><Admin /></ProtectedRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
