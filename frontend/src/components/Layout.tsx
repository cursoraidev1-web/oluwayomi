import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { 
  Home, 
  Upload, 
  Film, 
  Settings, 
  LogOut,
  Scissors,
  Zap
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'

export default function Layout() {
  const { logout, user } = useAuthStore()
  const navigate = useNavigate()
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  
  const navItems = [
    { to: '/', icon: Home, label: 'Dashboard' },
    { to: '/upload', icon: Upload, label: 'Upload' },
    { to: '/clips', icon: Film, label: 'Clips' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ]
  
  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
              <Scissors className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">ClipForge</h1>
              <p className="text-xs text-slate-400">Auto Clips & Posts</p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                      isActive
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        
        {/* Features highlight */}
        <div className="p-4 mx-4 mb-4 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 border border-primary-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-primary-400" />
            <span className="text-sm font-semibold text-primary-400">100% Free</span>
          </div>
          <p className="text-xs text-slate-400">
            No subscriptions. All processing is local and self-hosted.
          </p>
        </div>
        
        {/* User section */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.email[0].toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.email}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
      
      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
