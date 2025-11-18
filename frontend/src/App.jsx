import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import ScreeningPage from './ScreeningPage';
import Login from './Login';
import Register from './Register';
import ProtectedRoute from './ProtectedRoute';
import { getHealth } from './lib/api';
import { Shield, LogOut } from 'lucide-react';

const Header = () => {
  const { user, logout } = useAuth();
  
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">ComplianceAI Pro</h1>
            <span className="ml-3 text-xs text-blue-700 font-semibold">Enterprise Screening</span>
          </div>
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <span className="text-sm text-gray-700">Welcome, {user.email}</span>
                <button
                  onClick={() => {
                    logout();
                    window.location.href = '/login';
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm text-white bg-red-600 hover:bg-red-700 rounded-md transition font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-blue-600 hover:text-blue-800 font-medium">Login</Link>
                <Link to="/register" className="text-sm text-blue-600 hover:text-blue-800 font-medium">Register</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

function HomePage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const data = await getHealth();
      setHealth(data);
    } catch (err) {
      setHealth({ status: 'error', message: 'Backend connection failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Enhanced PEP & Sanctions Screening
          </h1>
          <p className="text-xl text-gray-600">
            AI-powered screening against global watchlists with intelligent risk analysis
          </p>
        </div>

        <div className="max-w-md mx-auto mb-8">
          <div className={`p-4 rounded-lg text-center ${
            health?.status === 'ok' ? 'bg-green-50 text-green-800' : 
            health?.status === 'error' ? 'bg-red-50 text-red-800' :
            'bg-yellow-50 text-yellow-800'
          }`}>
            <div className="font-semibold">
              {loading ? '🔄 Checking system status...' : `✅ ${health?.message}`}
            </div>
            {!loading && health?.status === 'ok' && health.ai_enabled && (
              <div className="text-sm mt-1">🤖 AI Analysis Enabled</div>
            )}
          </div>
        </div>

        <ScreeningPage />
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
