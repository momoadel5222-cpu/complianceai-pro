import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, AlertCircle, CheckCircle, XCircle, Download, Clock, History, Crown, Shield, Award } from 'lucide-react';
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
  // PEP fields
  is_pep?: boolean;
  pep_level?: 'direct' | 'associate' | 'family';
  position?: string;
  jurisdiction?: string;
  risk_score?: number;
}

interface SearchResult {
  screening_id: string;
  status: 'match' | 'potential_match' | 'no_match';
  matches: Match[];
}

interface HistoryItem {
  id: string;
  search_term: string;
  search_type: string;
  status: string;
  match_count: number;
  highest_match_score: number;
  created_at: string;
}

export default function ScreeningPage() {
  const { session } = useAuth();
  const [entityName, setEntityName] = useState('');
  const [entityType, setEntityType] = useState<'individual' | 'entity'>('individual');
  const [searchFilter, setSearchFilter] = useState<'all' | 'sanctions' | 'peps'>('all');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [searchHistory, setSearchHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (session?.access_token) {
      fetchSearchHistory();
    }
  }, [session]);

  const fetchSearchHistory = async () => {
    if (!session?.access_token) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/sanctions/history`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });
      setSearchHistory(response.data.data || []);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const handleScreen = async () => {
    if (!entityName.trim()) {
      setError('Please enter a name to search');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const headers = session?.access_token ? {
        Authorization: `Bearer ${session.access_token}`
      } : {};

      const response = await axios.post(
        `${API_BASE_URL}/sanctions/screen`,
        {
          name: entityName,
          type: entityType,
        },
        { headers }
      );

      if (response.data.success) {
        let filteredMatches = response.data.data.matches;
        
        // Apply filter
        if (searchFilter === 'sanctions') {
          filteredMatches = filteredMatches.filter((m: Match) => !m.is_pep);
        } else if (searchFilter === 'peps') {
          filteredMatches = filteredMatches.filter((m: Match) => m.is_pep);
        }
        
        setResult({
          ...response.data.data,
          matches: filteredMatches
        });
        
        if (session?.access_token) {
          setTimeout(() => fetchSearchHistory(), 1000);
        }
      } else {
        setError(response.data.error || 'Search failed');
      }
    } catch (err) {
      console.error('Screening error:', err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error || err.message || 'Connection error');
      } else {
        setError('An unexpected error occurred');
      }
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

  const getPepBadge = (pepLevel?: string) => {
    if (!pepLevel) return null;
    
    const badges = {
      direct: { color: 'bg-purple-100 text-purple-800', icon: <Crown className="w-3 h-3" />, text: 'Direct PEP' },
      associate: { color: 'bg-blue-100 text-blue-800', icon: <Award className="w-3 h-3" />, text: 'PEP Associate' },
      family: { color: 'bg-indigo-100 text-indigo-800', icon: <Award className="w-3 h-3" />, text: 'PEP Family' },
    };
    
    const badge = badges[pepLevel as keyof typeof badges] || badges.direct;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold ${badge.color}`}>
        {badge.icon}
        {badge.text}
      </span>
    );
  };

  const getRiskBadge = (riskScore?: number, isPep?: boolean, listSource?: string) => {
    // Calculate risk if not provided
    let score = riskScore || 0;
    if (!riskScore) {
      if (listSource?.includes('OFAC') || listSource?.includes('UN')) score += 80;
      if (isPep) score += 50;
    }
    
    if (score >= 80) {
      return <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-bold rounded">HIGH RISK</span>;
    } else if (score >= 50) {
      return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-bold rounded">MEDIUM RISK</span>;
    } else {
      return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-bold rounded">LOW RISK</span>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-red-800">Error</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Search Filter
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setSearchFilter('all')}
                    className={`px-3 py-2 border-2 rounded-lg text-sm font-medium transition ${
                      searchFilter === 'all'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setSearchFilter('sanctions')}
                    className={`px-3 py-2 border-2 rounded-lg text-sm font-medium transition ${
                      searchFilter === 'sanctions'
                        ? 'border-red-500 bg-red-50 text-red-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    <Shield className="w-4 h-4 inline mr-1" />
                    Sanctions
                  </button>
                  <button
                    onClick={() => setSearchFilter('peps')}
                    className={`px-3 py-2 border-2 rounded-lg text-sm font-medium transition ${
                      searchFilter === 'peps'
                        ? 'border-purple-500 bg-purple-50 text-purple-700'
                        : 'border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    <Crown className="w-4 h-4 inline mr-1" />
                    PEPs
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
                    Run Sanctions & PEP Screen
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
                      {result.matches.length} match{result.matches.length !== 1 ? 'es' : ''} found
                      {result.matches.length > 0 && ' - Review required'}
                    </p>
                  </div>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition">
                  <Download className="w-4 h-4" />
                  Export
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
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">
                              Match #{idx + 1}
                            </span>
                            <span className="bg-gray-100 text-gray-800 text-xs font-bold px-2 py-1 rounded">
                              {match.entity_type}
                            </span>
                            {match.is_pep && getPepBadge(match.pep_level)}
                            {getRiskBadge(match.risk_score, match.is_pep, match.list_source)}
                          </div>
                          <h5 className="text-xl font-bold text-gray-900 mb-1">{match.entity_name}</h5>
                          <p className="text-sm text-gray-600">
                            Source: {match.list_source} • Program: {match.program}
                          </p>
                        </div>
                        <div className="text-right ml-4">
                          <div className="text-3xl font-bold text-blue-600">
                            {(match.best_score * 100).toFixed(1)}%
                          </div>
                          <p className="text-xs text-gray-600">Confidence</p>
                        </div>
                      </div>

                      {/* PEP Specific Info */}
                      {match.is_pep && (
                        <div className="mb-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                          <h6 className="font-semibold text-purple-900 mb-2 flex items-center gap-2">
                            <Crown className="w-4 h-4" />
                            PEP Information
                          </h6>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                            {match.position && (
                              <div>
                                <p className="text-purple-700 font-medium">Position</p>
                                <p className="text-purple-900">{match.position}</p>
                              </div>
                            )}
                            {match.jurisdiction && (
                              <div>
                                <p className="text-purple-700 font-medium">Jurisdiction</p>
                                <p className="text-purple-900">{match.jurisdiction}</p>
                              </div>
                            )}
                            <div>
                              <p className="text-purple-700 font-medium">PEP Level</p>
                              <p className="text-purple-900 capitalize">{match.pep_level || 'Direct'}</p>
                            </div>
                          </div>
                        </div>
                      )}

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
                            {match.aliases.slice(0, 10).map((alias, i) => (
                              <span key={i} className="bg-gray-100 px-2 py-1 rounded text-sm">
                                {alias}
                              </span>
                            ))}
                            {match.aliases.length > 10 && (
                              <span className="text-sm text-gray-500">+{match.aliases.length - 10} more</span>
                            )}
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
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">OFAC Sanctions</span>
                <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                  Active
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700">UN Sanctions</span>
                <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                  Active
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-700 flex items-center gap-1">
                  <Crown className="w-3 h-3" />
                  PEP Database
                </span>
<span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-1 rounded">
                  Active
                </span>
              </div>
            </div>
          </div>

          {/* Search History */}
          {searchHistory.length > 0 && (
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Recent Searches
                </h3>
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  {showHistory ? 'Hide' : 'Show All'}
                </button>
              </div>
              <div className="space-y-2">
                {searchHistory.slice(0, showHistory ? undefined : 5).map((item) => (
                  <div key={item.id} className="py-2 border-b last:border-0">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-700 truncate">
                          {item.search_term}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-1 rounded ml-2 ${
                        item.status === 'match' ? 'bg-red-100 text-red-700' :
                        item.status === 'potential_match' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {item.match_count} match{item.match_count !== 1 ? 'es' : ''}
                      </span>
                    </div>
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