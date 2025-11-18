import { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle, XCircle, Download, Clock, History, Crown, Shield, Award, FileSpreadsheet, FileText, FileDown, Brain, TrendingUp, AlertTriangle, LogOut } from 'lucide-react';

const API_BASE_URL = 'http://localhost:10000/api';  // FIXED: Correct API endpoint

interface Match {
  entity_name: string;
  entity_type: string;
  list_source: string;
  program: string;
  nationalities: string[];
  date_of_birth: string;
  match_score: number;
}

interface SearchResult {
  name: string;
  match_found: boolean;
  matches: Match[];
  risk_level: string;
  total_matches: number;
  recommended_action: string;
  ai_analysis?: string;
}

export default function ScreeningPage() {
  const [entityName, setEntityName] = useState('Mostafa Madbouly');  // PRELOAD
  const [country, setCountry] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [entityType, setEntityType] = useState<'individual' | 'entity' | 'both'>('individual');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    // Mock stats for demo
    setStats({
      total_sanctions: 1250000,
      status: 'LIVE'
    });
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
      const response = await fetch(`${API_BASE_URL}/screen`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: entityName,
          type: entityType,  // Send entityType
          nationality: country || null,
          date_of_birth: dateOfBirth || null
        }),
      });

      if (!response.ok) {
        throw new Error('Screening failed');
      }

      const data = await response.json();
      
      // Transform OUR backend response to YOUR interface EXACTLY
      const transformedResult: SearchResult = {
        name: data.name,
        match_found: data.match_found,
        matches: data.matches.map((match: any) => ({
          entity_name: match.name || match.entity_name,
          entity_type: match.is_pep ? 'individual PEP' : 'sanctions',
          list_source: match.list_type || match.list_source,
          program: match.program,
          nationalities: typeof match.nationalities === 'string' 
            ? match.nationalities.split(', ') 
            : match.nationalities || [],
          date_of_birth: match.date_of_birth || 'Not specified',
          match_score: match.confidence || match.match_score || 0
        })),
        total_matches: data.matches.length,
        risk_level: data.risk_level || 'LOW',
        recommended_action: data.matches.length > 0 ? 'REVIEW' : 'APPROVE',
        ai_analysis: data.matches.length > 0 
          ? `Found ${data.matches.length} high-confidence match${data.matches.length > 1 ? 'es' : ''} in ${data.matches[0].program || 'PEP list'}.`
          : 'No matches found across all watchlists.'
      };

      setResult(transformedResult);
    } catch (err: any) {
      setError(err.message || 'Connection error - check if backend is running on port 10000');
    } finally {
      setLoading(false);
    }
  };

  // YOUR EXACT ORIGINAL FUNCTIONS - 100% UNCHANGED
  const getRiskColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH': case 'CRITICAL': return 'bg-red-50 border-red-300 text-red-900';
      case 'MEDIUM': return 'bg-yellow-50 border-yellow-300 text-yellow-900';
      case 'LOW': return 'bg-green-50 border-green-300 text-green-900';
      default: return 'bg-gray-50 border-gray-300 text-gray-900';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH': case 'CRITICAL': return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'MEDIUM': return <AlertCircle className="w-6 h-6 text-yellow-600" />;
      case 'LOW': return <CheckCircle className="w-6 h-6 text-green-600" />;
      default: return <XCircle className="w-6 h-6 text-gray-600" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action.toUpperCase()) {
      case 'ESCALATE': case 'BLOCK': return 'bg-red-600 text-white';
      case 'REVIEW': return 'bg-yellow-600 text-white';
      case 'APPROVE': case 'CLEAR': return 'bg-green-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const exportToJSON = () => {
    if (!result) return;
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `compliance-report-${entityName}-${Date.now()}.json`;
    link.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/30">
      {/* Header */}
      <nav className="bg-white shadow-lg border-b border-blue-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl shadow-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                ComplianceAI Pro
              </h1>
              <p className="text-xs text-blue-700 font-semibold">Enterprise Sanctions Intelligence</p>
            </div>
          </div>
          <button
            onClick={() => alert('Sign out functionality')}
            className="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-red-600 hover:bg-red-700 rounded-lg transition shadow-md font-semibold"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Search Section - YOUR EXACT CODE */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 bg-gradient-to-br from-slate-100 to-slate-200 rounded-xl">
                  <Search className="w-6 h-6 text-slate-700" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">Sanctions Screening</h2>
                  <p className="text-sm text-slate-600">Global watchlist and sanctions list monitoring</p>
                </div>
              </div>

              {error && (
                <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-600 rounded flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-red-800">Error</p>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              )}

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Entity Name *
                  </label>
                  <input
                    type="text"
                    value={entityName}
                    onChange={(e) => setEntityName(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleScreen()}
                    className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition shadow-sm"
                    placeholder="Enter individual or organization name..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Entity Type *
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => setEntityType('individual')}
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm ${
                        entityType === 'individual'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-200'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      Individual
                    </button>
                    <button
                      onClick={() => setEntityType('entity')}
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm ${
                        entityType === 'entity'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-200'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      Entity
                    </button>
                    <button
                      onClick={() => setEntityType('both')}
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm ${
                        entityType === 'both'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-200'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      Both
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Country (Optional)
                    </label>
                    <input
                      type="text"
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition shadow-sm"
                      placeholder="e.g., Russia, Iran"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">
                      Date of Birth (Optional)
                    </label>
                    <input
                      type="date"
                      value={dateOfBirth}
                      onChange={(e) => setDateOfBirth(e.target.value)}
                      className="w-full px-4 py-3.5 border-2 border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition shadow-sm"
                    />
                  </div>
                </div>

                <button
                  onClick={handleScreen}
                  disabled={loading || !entityName.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-4 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg shadow-purple-200"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Screening in Progress...
                    </>
                  ) : (
                    <>
                      <Shield className="w-5 h-5" />
                      Screen Entity
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* AI Analysis Results */}
            {result && (
              <div className={`rounded-lg shadow-md border-2 p-8 ${getRiskColor(result.risk_level)}`}>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-4">
                    {getRiskIcon(result.risk_level)}
                    <div>
                      <h3 className="text-2xl font-bold">{result.risk_level} RISK LEVEL</h3>
                      <p className="text-sm opacity-80 font-medium">
                        {result.total_matches} match{result.total_matches !== 1 ? 'es' : ''} identified
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-4 py-2 rounded-lg font-bold text-sm uppercase tracking-wide ${getActionColor(result.recommended_action)}`}>
                      {result.recommended_action}
                    </span>
                  </div>
                </div>

                {/* AI Compliance Analysis */}
                {result.ai_analysis && (
                  <div className="mb-6 p-6 bg-white/90 backdrop-blur rounded-lg border-2 border-slate-300 shadow-sm">
                    <div className="flex items-start gap-3 mb-3">
                      <Brain className="w-6 h-6 text-slate-700 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h4 className="font-bold text-lg text-slate-900 mb-1">
                          Compliance Risk Analysis
                        </h4>
                        <p className="text-sm text-slate-600 font-semibold uppercase tracking-wide">
                          Automated Intelligence Assessment
                        </p>
                      </div>
                    </div>
                    <div className="pl-9">
                      <p className="text-sm leading-relaxed text-slate-800 bg-slate-50 p-4 rounded border border-slate-200 font-medium">
                        {result.ai_analysis}
                      </p>
                    </div>
                  </div>
                )}

                {/* Export Button */}
                {result.matches.length > 0 && (
                  <div className="flex justify-end mb-6">
                    <button
                      onClick={exportToJSON}
                      className="flex items-center gap-2 px-5 py-2.5 bg-white rounded-xl hover:bg-gray-50 transition border-2 border-gray-300 shadow-sm font-semibold text-sm"
                    >
                      <Download className="w-4 h-4" />
                      Export Report
                    </button>
                  </div>
                )}

                {/* Detailed Matches */}
                {result.matches.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="font-bold text-base flex items-center gap-2 text-slate-900 uppercase tracking-wide">
                      <TrendingUp className="w-5 h-5" />
                      Match Details
                    </h4>
                    {result.matches.map((match, idx) => (
                      <div key={idx} className="bg-white/95 backdrop-blur rounded-lg p-6 shadow-sm border-2 border-slate-200">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-2 mb-3">
                              <span className="bg-slate-800 text-white text-xs font-bold px-3 py-1 rounded uppercase tracking-wide">
                                Match #{idx + 1}
                              </span>
                              <span className="bg-slate-200 text-slate-800 text-xs font-bold px-3 py-1 rounded uppercase">
                                {match.entity_type}
                              </span>
                              <span className="bg-slate-100 text-slate-700 text-xs font-semibold px-3 py-1 rounded border border-slate-300">
                                {match.list_source}
                              </span>
                            </div>
                            <h5 className="text-xl font-bold text-slate-900">{match.entity_name}</h5>
                            <p className="text-sm text-slate-600 font-medium">
                              Program: <span className="font-bold text-slate-800">{match.program}</span>
                            </p>
                          </div>
                          <div className="text-right ml-4">
                            <div className="text-3xl font-bold text-slate-900">
                              {(match.match_score * 100).toFixed(0)}%
                            </div>
                            <p className="text-xs text-slate-600 font-bold uppercase tracking-wide">Match Score</p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm pt-4 border-t-2 border-slate-200">
                          <div>
                            <p className="text-slate-500 mb-1 font-bold text-xs uppercase tracking-wide">Nationalities</p>
                            <p className="text-slate-900 font-semibold">
                              {match.nationalities?.length > 0 ? match.nationalities.join(', ').toUpperCase() : 'Not specified'}
                            </p>
                          </div>
                          <div>
                            <p className="text-slate-500 mb-1 font-bold text-xs uppercase tracking-wide">Date of Birth</p>
                            <p className="text-slate-900 font-semibold">{match.date_of_birth || 'Not specified'}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {result.total_matches === 0 && (
                  <div className="text-center py-8">
                    <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                    <h4 className="text-xl font-bold text-gray-900 mb-2">Clear Status</h4>
                    <p className="text-gray-600">No sanctions or compliance concerns identified</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Stats Card */}
            {stats && (
              <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-6">
                <h3 className="font-bold text-base mb-4 flex items-center gap-2 text-slate-900">
                  <Shield className="w-5 h-5 text-blue-600" />
                  Database Coverage
                </h3>
                <div className="text-center mb-4 p-6 bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl shadow-lg">
                  <div className="text-4xl font-bold text-white mb-1">
                    {stats.total_sanctions?.toLocaleString()}
                  </div>
                  <p className="text-xs text-blue-100 font-semibold uppercase tracking-wide">Records Monitored</p>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-2 border-green-200 shadow-sm">
                    <span className="text-slate-700 font-semibold">Status</span>
                    <span className="text-green-600 font-bold uppercase text-xs tracking-wide">
                      {stats.status}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Coverage Panel */}
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-6">
              <h3 className="font-bold text-base mb-4 flex items-center gap-2 text-slate-900">
                <Shield className="w-5 h-5 text-blue-600" />
                Live Sanctions Feed
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'UN Security Council', status: 'live' },
                  { name: 'OFAC Sanctions List', status: 'live' },
                  { name: 'UK-HMT Sanctions', status: 'live' },
                  { name: 'Domestic Lists', status: 'live' }
                ].map((source) => (
                  <div key={source.name} className="flex justify-between items-center p-3.5 bg-slate-50 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse shadow-lg shadow-red-300"></div>
                        <div className="absolute inset-0 w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></div>
                      </div>
                      <span className="text-sm font-semibold text-slate-700">{source.name}</span>
                    </div>
                    <span className="text-xs font-bold text-green-700 bg-green-100 px-3 py-1 rounded-full uppercase tracking-wide">
                      LIVE
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Features */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-xl border-2 border-blue-200 p-6">
              <h3 className="font-bold text-base mb-4 flex items-center gap-2 text-slate-900">
                <Brain className="w-5 h-5 text-blue-600" />
                Compliance Intelligence Features
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-blue-100 shadow-sm">
                  <Shield className="w-6 h-6 text-slate-700 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <p className="font-bold text-lg text-slate-900 mb-1">
                      Risk Assessment
                    </p>
                    <p className="text-slate-600 font-semibold uppercase tracking-wide">
                      Automated compliance risk scoring
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-purple-100 shadow-sm">
                  <TrendingUp className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <p className="font-bold text-lg text-slate-900 mb-1">
                      Match Analysis
                    </p>
                    <p className="text-slate-600 font-semibold uppercase tracking-wide">
                      Intelligent entity verification
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-blue-100 shadow-sm">
                  <AlertTriangle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <p className="font-bold text-lg text-slate-900 mb-1">
                      Action Recommendations
                    </p>
                    <p className="text-slate-600 font-semibold uppercase tracking-wide">
                      Decision support guidance
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 bg-gradient-to-r from-blue-600 to-blue-800 shadow-2xl py-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/10 rounded-lg backdrop-blur">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">ComplianceAI Pro</p>
                <p className="text-xs text-blue-100">Professional Sanctions Screening Platform</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-white font-semibold">
                Powered by <span className="font-bold">Mohamed Emam</span>
              </p>
              <p className="text-xs text-blue-100 mt-1">Compliance AI © 2024</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
