import { useState } from 'react';
import { Search, AlertTriangle, CheckCircle, XCircle, Shield } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://complianceai-backend-7n50.onrender.com/api';

function ScreeningPage() {
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
      console.log('🔍 Searching:', searchTerm, 'Type:', entityType);
      console.log('🌐 API URL:', `${API_BASE_URL}/sanctions/screen`);
      
      const response = await fetch(`${API_BASE_URL}/sanctions/screen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: searchTerm, type: entityType }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Response data:', data);

      if (data.success) {
        setResults(data.data);
        setSearchHistory(prev => [{
          id: data.data.screening_id,
          name: searchTerm,
          type: entityType,
          status: data.data.status,
          timestamp: new Date().toISOString(),
          matchCount: data.data.matches?.length || 0
        }, ...prev.slice(0, 9)]);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch (err: any) {
      console.error('❌ Search error:', err);
      setError(`Failed to connect to server: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatScore = (score: number) => (score * 100).toFixed(1) + '%';

  return (
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
          <h3 className="font-bold text-red-800 mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {results && results.matches && results.matches.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900">Results: {results.matches.length} match(es) found</h3>
            <div className="bg-blue-100 px-3 py-1 rounded-full">
              <span className="text-sm font-semibold text-blue-800">Screening ID: {results.screening_id}</span>
            </div>
          </div>
          {results.matches.map((match: any, idx: number) => (
            <div key={idx} className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 hover:shadow-xl transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <h4 className="text-xl font-bold text-gray-900">{match.entity_name}</h4>
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-semibold">
                  {formatScore(match.best_score)}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-semibold text-gray-700">List Source:</span>
                  <p className="text-gray-600">{match.list_source}</p>
                </div>
                <div>
                  <span className="font-semibold text-gray-700">Program:</span>
                  <p className="text-gray-600">{match.program}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {results && results.matches && results.matches.length === 0 && (
        <div className="bg-green-50 border-l-4 border-green-500 rounded-xl p-6">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div>
              <h3 className="text-xl font-bold text-green-800">No Matches Found</h3>
              <p className="text-green-700">The entity {searchTerm} did not match any sanctions lists.</p>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default ScreeningPage;
