import { useState } from 'react';
import axios from 'axios';
import { Search, Shield, AlertCircle, CheckCircle, XCircle, Download, Clock } from 'lucide-react';
import { useAuth } from './AuthContext';

const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:3000/api' 
  : 'https://shiny-spoon-96qrv99gxxvf74pq-3000.app.github.dev/api';

interface Match {
  id: string;
  entity_name: string;
  entity_type: string;
  list_source: string;
  program: string;
  nationalities: string[];
  date_listed: string;
  aliases: string[];
  best_score: number;
  remarks?: string;
  date_of_birth_text?: string;
}

interface SearchResult {
  screening_id: string;
  status: 'match' | 'potential_match' | 'no_match';
  matches: Match[];
}

interface SearchHistory {
  term: string;
  status: string;
  timestamp: Date;
}

export default function ScreeningPage() {
  const { user } = useAuth();
  const [entityName, setEntityName] = useState('');
  const [entityType, setEntityType] = useState<'individual' | 'entity'>('individual');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);

  const handleScreen = async () => {
    if (!entityName.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/sanctions/screen`, {
        name: entityName,
        type: entityType,
      });

      setResult(response.data.data);
      setSearchHistory(prev => [
        { term: entityName, status: response.data.data.status, timestamp: new Date() },
        ...prev.slice(0, 9)
      ]);
    } catch (error) {
      console.error('Screening error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'match': return 'bg-red-50 border-red-200 text-red-800';
      case 'potential_match': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'no_match': return 'bg-green-50 border-green-200 text-green-800';
      default: return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'match': return <AlertCircle className="w-6 h-6 text-red-600" />;
      case 'potential_match': return <AlertCircle className="w-6 h-6 text-yellow-600" />;
      case 'no_match': return <CheckCircle className="w-6 h-6 text-green-600" />;
      default: return <XCircle className="w-6 h-6 text-gray-600" />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Search Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Search Card */}
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center gap-3 mb-6">
              <Search className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Screen Entity</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Entity Name
                </label>
                <input
                  type="text"
                  value={entityName}
                  onChange={(e) => setEntityName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleScreen()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter name or organization..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Entity Type
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setEntityType('individual')}
                    className={`px-4 py-3 border-2 rounded-lg font-medium transition ${
                      entityType === 'individual'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    👤 Individual
                  </button>
                  <button
                    onClick={() => setEntityType('entity')}
                    className={`px-4 py-3 border-2 rounded-lg font-medium transition ${
                      entityType === 'entity'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    🏢 Organization
                  </button>
                </div>
              </div>

              <button
                onClick={handleScreen}
                disabled={loading || !entityName.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Screening...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Run Sanctions Screen
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className={`rounded-2xl shadow-lg p-6 border-2 ${getStatusColor(result.status)}`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(result.status)}
                  <div>
                    <h3 className="text-xl font-bold capitalize">{result.status.replace('_', ' ')}</h3>
                    <p className="text-sm opacity-75">
                      {result.matches.length} potential match{result.matches.length !== 1 ? 'es' : ''} found
                      {result.matches.length > 0 && ' - Review required'}
                    </p>
                  </div>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition">
                  <Download className="w-4 h-4" />
                  Export Report
                </button>
              </div>

              {result.matches.length > 0 && (
                <div className="mt-6 space-y-4">
                  <h4 className="font-bold text-lg flex items-center gap-2">
                    📋 Detailed Match Analysis
                  </h4>
                  {result.matches.map((match, idx) => (
                    <div key={match.id} className="bg-white rounded-lg p-6 shadow">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">
                              Match #{idx + 1}
                            </span>
                            <span className="bg-purple-100 text-purple-800 text-xs font-bold px-2 py-1 rounded">
                              {match.entity_type}
                            </span>
                          </div>
                          <h5 className="text-xl font-bold text-gray-900">{match.entity_name}</h5>
                          <p className="text-sm text-gray-600">
                            List Source: {match.list_source} • Program: {match.program}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-3xl font-bold text-blue-600">
                            {(match.best_score * 100).toFixed(1)}%
                          </div>
                          <p className="text-xs text-gray-600">Confidence</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-600 mb-1">🌍 Nationalities</p>
                          <p className="font-semibold">
                            {match.nationalities?.length > 0 ? match.nationalities.join(', ') : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-600 mb-1">📅 Date Listed</p>
                          <p className="font-semibold">{match.date_listed || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 mb-1">🎯 Program</p>
                          <p className="font-semibold">{match.program}</p>
                        </div>
                        <div>
                          <p className="text-gray-600 mb-1">📊 Match Score</p>
                          <p className="font-semibold">{(match.best_score * 100).toFixed(1)}%</p>
                        </div>
                      </div>

                      {match.aliases && match.aliases.length > 0 && (
                        <div className="mt-4">
                          <p className="text-sm text-gray-600 mb-2">Aliases:</p>
                          <div className="flex flex-wrap gap-2">
                            {match.aliases.map((alias, i) => (
                              <span key={i} className="bg-gray-100 px-2 py-1 rounded text-sm">
                                {alias}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Coverage Panel */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              🛡️ Coverage
            </h3>
            <div className="space-y-3">
              {['OFAC SDN', 'UN Sanctions', 'EU Sanctions', 'MLCU Egypt'].map((source) => (
                <div key={source} className="flex justify-between items-center">
                  <span className="text-sm text-gray-700">{source}</span>
                  <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                    Active
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Quick Stats
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Last Update:</span>
                <span className="font-semibold">Today</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Database Size:</span>
                <span className="font-semibold">45K+ records</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Match Accuracy:</span>
                <span className="font-semibold text-green-600">98.5%</span>
              </div>
            </div>
          </div>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="font-bold text-lg mb-4">Recent Searches</h3>
              <div className="space-y-2">
                {searchHistory.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center text-sm py-2 border-b last:border-0">
                    <span className="text-gray-700 truncate">{item.term}</span>
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      item.status === 'match' ? 'bg-red-100 text-red-700' :
                      item.status === 'potential_match' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {item.status.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
