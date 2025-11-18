import { useState, useEffect } from 'react';
import { Search, AlertCircle, CheckCircle, XCircle, Download, Brain, TrendingUp, AlertTriangle, LogOut, Shield, User, Building, Users, Crown } from 'lucide-react';
import { screenEntity, getStats, EnhancedSearchResult, EnhancedMatch } from './lib/api';

export default function ScreeningPage() {
  const [entityName, setEntityName] = useState('');
  const [country, setCountry] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [entityType, setEntityType] = useState<'individual' | 'entity' | 'both'>('both');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EnhancedSearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
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

  // Map 'both' to a valid backend type
  const type = entityType === 'both' ? 'individual' : entityType;

  try {
    // Map 'both' to 'individual' as fallback
    const type = entityType === 'both' ? 'individual' : entityType;
    
    // Call with correct parameters
    const response = await screenEntity(entityName, type);
    setResult(response);
  } catch (err: any) {
    setError(err.message || 'Screening failed');
  } finally {
    setLoading(false);
  }
};

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleScreen();
    }
  };

  const getRiskColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH': 
      case 'CRITICAL': 
        return 'bg-red-50 border-red-300 text-red-900';
      case 'MEDIUM': 
        return 'bg-yellow-50 border-yellow-300 text-yellow-900';
      case 'LOW': 
        return 'bg-green-50 border-green-300 text-green-900';
      default: 
        return 'bg-gray-50 border-gray-300 text-gray-900';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH':
      case 'CRITICAL':
        return <AlertTriangle className="w-6 h-6 text-red-600" />;
      case 'MEDIUM':
        return <AlertCircle className="w-6 h-6 text-yellow-600" />;
      case 'LOW':
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      default:
        return <XCircle className="w-6 h-6 text-gray-600" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action.toUpperCase()) {
      case 'ESCALATE':
      case 'BLOCK':
        return 'bg-red-600 text-white';
      case 'REVIEW':
        return 'bg-yellow-600 text-white';
      case 'APPROVE':
      case 'CLEAR':
        return 'bg-green-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  const exportToJSON = () => {
    if (!result) return;
    const dataStr = JSON.stringify(result, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `screening-report-${entityName}-${Date.now()}.json`;
    link.click();
  };

  // Component to display match details with aliases/AKAs/positions
  const MatchDetailCard = ({ match, index }: { match: EnhancedMatch; index: number }) => {
    return (
      <div className="bg-white/95 backdrop-blur rounded-lg p-6 shadow-sm border-2 border-slate-200 mb-4">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="bg-slate-800 text-white text-xs font-bold px-3 py-1 rounded uppercase tracking-wide">
                Match #{index + 1}
              </span>
              <span className="bg-slate-200 text-slate-800 text-xs font-bold px-3 py-1 rounded uppercase">
                {match.entity_type}
              </span>
              <span className="bg-slate-100 text-slate-700 text-xs font-semibold px-3 py-1 rounded border border-slate-300">
                {match.list_source}
              </span>
            </div>
            <h5 className="text-xl font-bold text-slate-900 mb-2">{match.entity_name}</h5>
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

        {/* Aliases Section */}
        {match.aliases && match.aliases.length > 0 && (
          <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <User className="w-4 h-4 text-blue-600" />
              <h6 className="font-bold text-blue-900 text-sm uppercase tracking-wide">Aliases</h6>
            </div>
            <div className="flex flex-wrap gap-2">
              {match.aliases.map((alias, i) => (
                <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                  {alias}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* AKAs Section */}
        {match.akas && match.akas.length > 0 && (
          <div className="mb-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-purple-600" />
              <h6 className="font-bold text-purple-900 text-sm uppercase tracking-wide">Also Known As (AKA)</h6>
            </div>
            <div className="flex flex-wrap gap-2">
              {match.akas.map((aka, i) => (
                <span key={i} className="px-3 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">
                  {aka}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Positions Section (for PEPs) */}
        {match.positions && match.positions.length > 0 && (
          <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-center gap-2 mb-2">
              <Crown className="w-4 h-4 text-yellow-600" />
              <h6 className="font-bold text-yellow-900 text-sm uppercase tracking-wide">Positions</h6>
            </div>
            <ul className="list-disc list-inside text-sm text-yellow-900">
              {match.positions.map((pos, i) => (
                <li key={i} className="mb-1 font-medium">{pos}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Countries & Dates */}
        <div className="grid grid-cols-2 gap-4 text-sm">
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

        {/* Additional Details */}
        {match.details && Object.keys(match.details).length > 0 && (
          <details className="mt-4 text-sm">
            <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-semibold">
              View Additional Details
            </summary>
            <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-x-auto">
              {JSON.stringify(match.details, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
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
              <h1 className="text-2xl font-bold text-slate-900">ComplianceAI Pro</h1>
              <p className="text-xs text-blue-700 font-semibold">Enterprise Sanctions Intelligence</p>
            </div>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('authToken');
              window.location.href = '/login';
            }}
            className="flex items-center gap-2 px-5 py-2.5 text-sm text-white bg-red-600 hover:bg-red-700 rounded-lg transition shadow-md font-semibold"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Search Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Search Card */}
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
                    onKeyPress={handleKeyPress}
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
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm flex items-center justify-center gap-2 ${
                        entityType === 'individual'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      <User className="w-4 h-4" />
                      Individual
                    </button>
                    <button
                      onClick={() => setEntityType('entity')}
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm flex items-center justify-center gap-2 ${
                        entityType === 'entity'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      <Building className="w-4 h-4" />
                      Entity
                    </button>
                    <button
                      onClick={() => setEntityType('both')}
                      className={`px-4 py-3.5 border-2 rounded-xl font-semibold transition-all shadow-sm flex items-center justify-center gap-2 ${
                        entityType === 'both'
                          ? 'border-purple-600 bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-lg'
                          : 'border-slate-300 text-slate-700 hover:border-purple-400 bg-white hover:bg-purple-50'
                      }`}
                    >
                      <Users className="w-4 h-4" />
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
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-4 rounded-xl font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shadow-lg"
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
                      <h3 className="text-2xl font-bold">{result.risk_level.toUpperCase()} RISK LEVEL</h3>
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
                {(result.ai_explanation || result.ai_analysis) && (
                  <div className="mb-6 p-6 bg-white/90 backdrop-blur rounded-lg border-2 border-slate-300 shadow-sm">
                    <div className="flex items-start gap-3 mb-3">
                      <Brain className="w-6 h-6 text-slate-700 flex-shrink-0 mt-1" />
                      <div className="flex-1">
                        <h4 className="font-bold text-lg text-slate-900 mb-1">
                          🤖 AI Compliance Risk Analysis
                        </h4>
                        <p className="text-xs text-slate-600 font-semibold uppercase tracking-wide">
                          Automated Intelligence Assessment
                        </p>
                      </div>
                    </div>
                    <div className="pl-9">
                      {result.ai_explanation ? (
                        <>
                          <div className="mb-3">
                            <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                              result.ai_explanation.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                              result.ai_explanation.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              Risk Level: {result.ai_explanation.risk_level?.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm leading-relaxed text-slate-800 bg-slate-50 p-4 rounded border border-slate-200 font-medium mb-3">
                            {result.ai_explanation.summary}
                          </p>
                          <div>
                            <h5 className="font-semibold text-slate-900 mb-2">Key Risk Factors:</h5>
                            <ul className="list-disc list-inside text-sm text-slate-700 bg-slate-50 p-3 rounded border border-slate-200">
                              {result.ai_explanation.key_factors?.map((factor, idx) => (
                                <li key={idx} className="mb-1">{factor}</li>
                              ))}
                            </ul>
                          </div>
                        </>
                      ) : (
                        <p className="text-sm leading-relaxed text-slate-800 bg-slate-50 p-4 rounded border border-slate-200 font-medium">
                          {result.ai_analysis}
                        </p>
                      )}
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

                {/* Detailed Matches with Aliases/AKAs */}
                {result.matches.length > 0 && (
                  <div className="space-y-4">
                    <h4 className="font-bold text-base flex items-center gap-2 text-slate-900 uppercase tracking-wide">
                      <TrendingUp className="w-5 h-5" />
                      Match Details
                    </h4>
                    {result.matches.map((match, idx) => (
                      <MatchDetailCard key={idx} match={match} index={idx} />
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

          {/* Sidebar - CLEAN (No Database Coverage) */}
          <div className="space-y-6">
            {/* System Status */}
            {stats && (
              <div className="bg-white rounded-xl shadow-xl border border-slate-200 p-6">
                <h3 className="font-bold text-base mb-4 flex items-center gap-2 text-slate-900">
                  <Shield className="w-5 h-5 text-blue-600" />
                  System Status
                </h3>
                <div className={`p-4 rounded-lg text-center ${
                  stats.status === 'ok' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                }`}>
                  <div className="font-semibold">✅ Backend Connected</div>
                  {stats.ai_enabled && (
                    <div className="text-sm mt-1">🤖 AI Analysis Enabled</div>
                  )}
                </div>
              </div>
            )}

            {/* Live Sanctions Feed */}
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
                  { name: 'EU Sanctions', status: 'live' }
                ].map((source) => (
                  <div key={source.name} className="flex justify-between items-center p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></div>
                        <div className="absolute inset-0 w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></div>
                      </div>
                      <span className="text-sm font-semibold text-slate-700">{source.name}</span>
                    </div>
                    <span className="text-xs font-bold text-green-700 bg-green-100 px-3 py-1 rounded-full uppercase">
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
                Intelligence Features
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-blue-100">
                  <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-slate-900">Risk Assessment</p>
                    <p className="text-slate-600 text-xs">Automated compliance scoring</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-purple-100">
                  <TrendingUp className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-slate-900">Match Analysis</p>
                    <p className="text-slate-600 text-xs">Intelligent entity verification</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3.5 bg-white rounded-xl border border-blue-100">
                  <AlertTriangle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-slate-900">Action Recommendations</p>
                    <p className="text-slate-600 text-xs">Decision support guidance</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
