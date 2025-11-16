// File: frontend/src/ScreeningPage.tsx
import { useState, useRef } from 'react';
import { Search, CheckCircle, Globe, Calendar, User, Building2, Hash, Filter, Upload, Download, X, Brain, AlertTriangle, Shield, Info } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://complianceai-backend-7n50.onrender.com/api';

interface RiskAssessment {
  score: number;
  level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  factors: string[];
}

interface SanctionMatch {
  entity_name: string;
  entity_type: string;
  program: string;
  list_source: string;
  nationalities: string[];
  aliases: string[];
  match_score: number;
  best_fuzzy_score: number;
  semantic_score?: number;
  combined_score: number;
  risk_assessment: RiskAssessment;
  ai_explanation?: string;
}

interface ScreeningResults {
  screening_id: string;
  status: 'match' | 'potential_match' | 'low_confidence_match' | 'no_match';
  matches: SanctionMatch[];
  query: {
    name: string;
    type: string;
    ai_enabled: boolean;
    ai_provider?: string;
  };
  timestamp: string;
}

function ScreeningPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [entityType, setEntityType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScreeningResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);
  
  // Advanced filters
  const [showFilters, setShowFilters] = useState(false);
  const [nationality, setNationality] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [program, setProgram] = useState('');
  const [minScore, setMinScore] = useState(0.6);
  const [country, setCountry] = useState('');
  const [gender, setGender] = useState('');
  
  // AI Features
  const [useAI, setUseAI] = useState(true);
  const [showAIExplanations, setShowAIExplanations] = useState(true);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload: any = { 
        name: searchTerm, 
        type: entityType,
        use_ai: useAI
      };
      
      if (nationality) payload.nationality = nationality;
      if (dateOfBirth) payload.date_of_birth = dateOfBirth;
      if (dateFrom) payload.date_from = dateFrom;
      if (dateTo) payload.date_to = dateTo;
      if (program) payload.program = program;
      if (country) payload.country = country;
      if (gender) payload.gender = gender;

      console.log('🔍 Searching with Compliance AI:', useAI, 'Payload:', payload);
      
      const response = await fetch(`${API_BASE_URL}/sanctions/screen`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      
      if (data.success) {
        setResults(data.data);
        setSearchHistory(prev => [data.data, ...prev.slice(0, 9)]);
      } else {
        setError(data.error || 'Search failed');
      }
    } catch (err) {
      setError('Network error: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300';
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'LOW': return 'bg-green-100 text-green-800 border-green-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'match': return 'bg-red-100 text-red-800';
      case 'potential_match': return 'bg-orange-100 text-orange-800';
      case 'low_confidence_match': return 'bg-yellow-100 text-yellow-800';
      case 'no_match': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ComplianceAI Screening
          </h1>
          <p className="text-lg text-gray-600">
            Advanced sanctions screening with compliance-enhanced risk assessment
          </p>
        </div>

        {/* Search Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8">
          <div className="flex flex-col lg:flex-row gap-4 mb-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Enter name to screen..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="individual">Individual</option>
              <option value="entity">Entity</option>
              <option value="vessel">Vessel</option>
            </select>

            <button
              onClick={handleSearch}
              disabled={loading || !searchTerm.trim()}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              ) : (
                <Search size={16} />
              )}
              {loading ? 'Screening...' : 'Screen'}
            </button>
          </div>

          {/* Compliance Enhanced Toggle and Filters */}
          <div className="flex flex-wrap gap-4 items-center">
            {/* Compliance Enhanced Toggle */}
            <div className="flex items-center gap-2 bg-blue-50 rounded-lg px-4 py-2">
              <Shield size={18} className="text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Compliance Enhanced</span>
              <label className="relative inline-flex items-center cursor-pointer ml-2">
                <input
                  type="checkbox"
                  checked={useAI}
                  onChange={(e) => setUseAI(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Filters Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <Filter size={16} />
              Filters
            </button>

            {/* Compliance Explanations Toggle */}
            {useAI && (
              <button
                onClick={() => setShowAIExplanations(!showAIExplanations)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Info size={16} />
                {showAIExplanations ? 'Hide Compliance' : 'Show Compliance'} Explanations
              </button>
            )}
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nationality
                  </label>
                  <input
                    type="text"
                    value={nationality}
                    onChange={(e) => setNationality(e.target.value)}
                    placeholder="e.g., Russian"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    placeholder="e.g., Russia"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All Genders</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date From
                  </label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date To
                  </label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Program
                  </label>
                  <input
                    type="text"
                    value={program}
                    onChange={(e) => setProgram(e.target.value)}
                    placeholder="e.g., OFAC"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Score
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={minScore}
                    onChange={(e) => setMinScore(parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <span className="text-sm text-gray-600">{minScore}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        {results && (
          <div className="space-y-6">
            {/* Summary Card */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Screening Results
                  </h2>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>Query: <strong>{results.query.name}</strong></span>
                    <span>Type: <strong>{results.query.type}</strong></span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(results.status)}`}>
                      {results.status.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    {results.query.ai_enabled && (
                      <span className="flex items-center gap-1 text-blue-600">
                        <Shield size={14} />
                        Compliance Enhanced ({results.query.ai_provider || 'Gemini'})
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(results.timestamp).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Matches */}
            {results.matches.length > 0 ? (
              <div className="space-y-4">
                {results.matches.map((match, index) => (
                  <div key={index} className="bg-white rounded-2xl shadow-xl p-6 border-l-4 border-blue-500">
                    <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4 mb-4">
                      <div className="flex-1">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {match.entity_name}
                          </h3>
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRiskBadgeColor(match.risk_assessment.level)}`}>
                              {match.risk_assessment.level} RISK
                            </span>
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                              {match.risk_assessment.score}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                          <div className="space-y-2">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Building2 size={14} />
                              <span>{match.entity_type}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Shield size={14} />
                              <span>{match.program}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Globe size={14} />
                              <span>{match.list_source}</span>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="text-sm">
                              <span className="font-medium">Match Score: </span>
                              <span className="text-blue-600">{match.match_score}</span>
                            </div>
                            <div className="text-sm">
                              <span className="font-medium">Fuzzy Score: </span>
                              <span className="text-green-600">{match.best_fuzzy_score}</span>
                            </div>
                            {match.semantic_score && (
                              <div className="text-sm">
                                <span className="font-medium">Semantic Score: </span>
                                <span className="text-purple-600">{match.semantic_score}</span>
                              </div>
                            )}
                            <div className="text-sm">
                              <span className="font-medium">Combined: </span>
                              <span className="text-orange-600 font-semibold">{match.combined_score}</span>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            {match.nationalities && match.nationalities.length > 0 && (
                              <div className="text-sm">
                                <span className="font-medium">Nationalities: </span>
                                <span>{match.nationalities.join(', ')}</span>
                              </div>
                            )}
                            {match.aliases && match.aliases.length > 0 && (
                              <div className="text-sm">
                                <span className="font-medium">Aliases: </span>
                                <span>{match.aliases.slice(0, 3).join(', ')}</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Risk Factors */}
                        {match.risk_assessment.factors.length > 0 && (
                          <div className="mb-4">
                            <h4 className="text-sm font-medium text-gray-700 mb-2">Risk Factors:</h4>
                            <div className="flex flex-wrap gap-2">
                              {match.risk_assessment.factors.map((factor, factorIndex) => (
                                <span key={factorIndex} className="px-2 py-1 bg-red-50 text-red-700 rounded text-xs">
                                  {factor}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Compliance Explanation */}
                        {useAI && showAIExplanations && match.ai_explanation && (
                          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                            <div className="flex items-center gap-2 mb-2">
                              <Shield size={16} className="text-blue-600" />
                              <h4 className="text-sm font-medium text-blue-900">Compliance Analysis</h4>
                            </div>
                            <p className="text-sm text-blue-800 leading-relaxed">
                              {match.ai_explanation}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
                <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No Matches Found</h3>
                <p className="text-gray-600">
                  No sanctions matches found for "{results.query.name}" with the current filters.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
            <div className="flex items-center gap-2 text-red-800 mb-2">
              <AlertTriangle size={20} />
              <h3 className="font-semibold">Error</h3>
            </div>
            <p className="text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ScreeningPage;
