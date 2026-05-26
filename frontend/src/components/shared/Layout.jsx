import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const NAV = [
  { path: '/dashboard', label: 'Review' },
  { path: '/upload', label: 'Upload' },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 flex items-center gap-6 h-12">
          <span className="font-semibold text-gray-900 text-sm">Breathe ESG</span>
          <div className="flex items-center gap-1 flex-1">
            {NAV.map((n) => (
              <Link
                key={n.path}
                to={n.path}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  pathname.startsWith(n.path)
                    ? 'bg-green-50 text-green-700 font-medium'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {n.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span>{user?.company_name}</span>
            <span className="text-gray-300">|</span>
            <span>{user?.username}</span>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-gray-600 text-xs underline"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
