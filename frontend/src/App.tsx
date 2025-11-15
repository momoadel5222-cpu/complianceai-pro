import { useState } from 'react';
import { Search, AlertTriangle, CheckCircle, XCircle, FileText, Calendar, Globe, Hash, User, Building2, TrendingUp, Clock, Download, Shield, Shield } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://complianceai-backend-7n50.onrender.com/api';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [entityType, setEntityType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch(`${API_BASE_URL}/sanctions/screen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: searchTerm, type: entityType }),
      });

      const data = await response.json();

      if (data.success) {
        setResults(data.data);
        setSearchHistory(prev => [{
          id: data.data.screening_id,
          name: searchTerm,
          type: entityType,
          status: data.data.status,
          timestamp: new Date().toISOString(),
          matchCount: data.data.matches.length
        }, ...prev.slice(0, 9)]);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch (err: any) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      match: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', icon: <AlertTriangle className="w-4 h-4" /> },
      potential_match: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', icon: <AlertTriangle className="w-4 h-4" /> },
      no_match: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', icon: <CheckCircle className="w-4 h-4" /> }
    };
    return badges[status as keyof typeof badges] || badges.no_match;
  };

  const formatScore = (score: number) => (score * 100).toFixed(1) + '%';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-white/10 backdrop-blur-sm p-3 rounded-xl">
                <Shield className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">ComplianceAI Pro</h1>
                <p className="text-blue-100 text-sm">Advanced Sanctions Screening Platform</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Search className="w-6 h-6 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Screen Entity</h2>
          </div>
          
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Entity Name</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleSearch()}
                placeholder="Enter full name or organization..."
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Entity Type</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setEntityType('individual')}
                  className={`py-3 px-4 rounded-xl border-2 font-medium ${
                    entityType === 'individual' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200'
                  }`}
                >
                  Individual
                </button>
                <button
                  onClick={() => setEntityType('entity')}
                  className={`py-3 px-4 rounded-xl border-2 font-medium ${
                    entityType === 'entity' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200'
                  }`}
                >
                  Organization
                </button>
              </div>
            </div>

            <button
              onClick={handleSearch}
              disabled={loading || !searchTerm.trim()}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Screening...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>Run Sanctions Screen</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-8 bg-red-50 border-l-4 border-red-500 rounded-xl p-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {results && results.matches && results.matches.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-gray-900">Results: {results.matches.length} match(es) found</h3>
            {results.matches.map((match: any, idx: number) => (
              <div key={idx} className="bg-white rounded-xl shadow-lg p-6 border">
                <h4 className="text-xl font-bold">{match.entity_name}</h4>
                <p className="text-gray-600">Confidence: {formatScore(match.best_score)}</p>
                <p className="text-sm text-gray-500">List: {match.list_source} • Program: {match.program}</p>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-600">
            <p className="mt-2 font-semibold text-blue-600">
              Developed by <a href="https://grc-consult-git-main-mohamed-emams-projects-621b38a2.vercel.app" target="_blank" rel="noopener noreferrer" className="hover:text-blue-800">Mohamed Emam - Compliance AI</a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
