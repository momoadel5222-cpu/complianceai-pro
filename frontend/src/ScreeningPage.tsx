import { useState, useRef } from 'react';
import { Search, CheckCircle, Globe, Calendar, User, Building2, Hash, Filter, Upload, Download, X } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://complianceai-backend-7n50.onrender.com/api';

function ScreeningPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [entityType, setEntityType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
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
  
  // Bulk screening
  const [showBulk, setShowBulk] = useState(false);
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkResults, setBulkResults] = useState<any>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload: any = { 
        name: searchTerm, 
        type: entityType,
        min_score: minScore
      };
      
      if (nationality) payload.nationality = nationality;
      if (dateOfBirth) payload.date_of_birth = dateOfBirth;
      if (dateFrom) payload.date_from = dateFrom;
      if (dateTo) payload.date_to = dateTo;
      if (program) payload.program = program;

      console.log('🔍 Searching with filters:', payload);
      
      const response = await fetch(`${API_BASE_URL}/sanctions/screen`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Response:', data);

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

  const handleBulkUpload = async () => {
    if (!bulkFile) return;
    
    setBulkLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', bulkFile);
      
      const response = await fetch(`${API_BASE_URL}/sanctions/bulk-screen`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setBulkResults(data.data);
      } else {
        setError(data.error || 'Bulk screening failed');
      }
    } catch (err: any) {
      setError(`Bulk screening error: ${err.message}`);
    } finally {
      setBulkLoading(false);
    }
  };

  const downloadTemplate = () => {
    const csv = 'name,type\nJohn Doe,individual\nAcme Corp,entity';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bulk_screening_template.csv';
    a.click();
  };

  const clearFilters = () => {
    setNationality('');
    setDateOfBirth('');
    setDateFrom('');
    setDateTo('');
    setProgram('');
    setMinScore(0.6);
  };

  const formatScore = (score: number) => (score * 100).toFixed(1) + '%';

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'match': return 'bg-red-50 border-red-200 text-red-800';
      case 'potential_match': return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'low_confidence_match': return 'bg-orange-50 border-orange-200 text-orange-800';
      default: return 'bg-green-50 border-green-200 text-green-800';
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Search Section */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Search className="w-6 h-6 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Screen Entity</h2>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showFilters ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
            <button
              onClick={() => setShowBulk(!showBulk)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showBulk ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700'}`}
            >
              <Upload className="w-4 h-4" />
              Bulk Screen
            </button>
          </div>
        </div>
        
        {/* Advanced Filters */}
        {showFilters && (
          <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-blue-900">Advanced Filters</h3>
              <button onClick={clearFilters} className="text-sm text-blue-600 hover:text-blue-800">
                Clear All
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nationality</label>
                <input
                  type="text"
                  value={nationality}
                  onChange={(e) => setNationality(e.target.value)}
                  placeholder="e.g., USA, UK"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                <input
                  type="text"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  placeholder="YYYY-MM-DD"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Program</label>
                <input
                  type="text"
                  value={program}
                  onChange={(e) => setProgram(e.target.value)}
                  placeholder="e.g., SDGT, IRAN"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Listed From</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Listed To</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Score: {(minScore * 100).toFixed(0)}%</label>
                <input
                  type="range"
                  min="0.5"
                  max="1"
                  step="0.05"
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}

        {/* Bulk Upload Section */}
        {showBulk && (
          <div className="mb-6 p-4 bg-purple-50 rounded-xl border border-purple-200">
            <h3 className="font-semibold text-purple-900 mb-4">Bulk Screening</h3>
            <div className="flex gap-4 items-center">
              <button
                onClick={downloadTemplate}
                className="px-4 py-2 bg-white border border-purple-300 rounded-lg flex items-center gap-2 hover:bg-purple-50"
              >
                <Download className="w-4 h-4" />
                Download Template
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={(e) => setBulkFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-white border border-purple-300 rounded-lg flex items-center gap-2 hover:bg-purple-50"
              >
                <Upload className="w-4 h-4" />
                {bulkFile ? bulkFile.name : 'Choose CSV File'}
              </button>
              {bulkFile && (
                <button
                  onClick={handleBulkUpload}
                  disabled={bulkLoading}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {bulkLoading ? 'Processing...' : 'Screen All'}
                </button>
              )}
            </div>
          </div>
        )}
        
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
                👤 Individual
              </button>
              <button
                onClick={() => setEntityType('entity')}
                className={`py-3 px-4 rounded-xl border-2 font-medium ${
                  entityType === 'entity' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200'
                }`}
              >
                🏢 Organization
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

      {/* Bulk Results */}
      {bulkResults && (
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold">Bulk Screening Results</h3>
            <button onClick={() => setBulkResults(null)} className="text-gray-500 hover:text-gray-700">
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-sm text-gray-600 mb-4">Screened {bulkResults.total_screened} entities</p>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {bulkResults.results.map((item: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium">{item.name}</span>
                  <span className="text-xs text-gray-500 ml-2">({item.type})</span>
                </div>
                <div className="flex items-center gap-3">
                  {item.top_match && (
                    <span className="text-xs text-gray-600">
                      {item.top_match.entity_name} ({formatScore(item.top_match.score)})
                    </span>
                  )}
                  <span className={`text-xs font-semibold px-3 py-1 rounded ${
                    item.status === 'match' ? 'bg-red-100 text-red-700' :
                    item.status === 'potential_match' ? 'bg-yellow-100 text-yellow-700' :
                    item.status === 'error' ? 'bg-gray-100 text-gray-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {item.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-8 bg-red-50 border-l-4 border-red-500 rounded-xl p-6">
          <h3 className="font-bold text-red-800 mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {results && (
        <div className={`rounded-2xl shadow-lg p-6 border-2 mb-8 ${getStatusColor(results.status)}`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold capitalize">
                {results.status.replace('_', ' ')}
              </h3>
              <p className="text-sm mt-1 opacity-75">
                {results.matches?.length || 0} match(es) found
              </p>
              {results.search_metadata && (
                <p className="text-xs mt-1 opacity-60">
                  Scanned: {results.search_metadata.total_scanned} | Filtered: {results.search_metadata.after_filters}
                </p>
              )}
            </div>
            <div className="text-right">
              <div className="text-sm opacity-75">Screening ID</div>
              <div className="font-mono text-xs">{results.screening_id}</div>
            </div>
          </div>
        </div>
      )}

      {results && results.matches && results.matches.length > 0 && (
        <div className="space-y-4">
          {results.matches.map((match: any, idx: number) => (
            <div key={idx} className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded">
                      Match #{idx + 1}
                    </span>
                    <span className="bg-purple-100 text-purple-800 text-xs font-bold px-2 py-1 rounded">
                      {match.entity_type}
                    </span>
                    <span className="bg-gray-100 text-gray-800 text-xs font-bold px-2 py-1 rounded">
                      {match.list_source}
                    </span>
                  </div>
                  <h4 className="text-xl font-bold text-gray-900">{match.entity_name}</h4>
                  {match.first_name && (
                    <p className="text-sm text-gray-600">
                      {match.first_name} {match.middle_name} {match.last_name}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-blue-600">
                    {formatScore(match.best_score)}
                  </div>
                  <p className="text-xs text-gray-600">Confidence</p>
                  <div className="mt-2 text-xs text-gray-500 space-y-1">
                    <div>Name: {formatScore(match.name_score)}</div>
                    <div>Phonetic: {formatScore(match.phonetic_score)}</div>
                    <div>Levenshtein: {formatScore(match.levenshtein_score)}</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                {match.nationalities && match.nationalities.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1 text-gray-600 mb-1">
                      <Globe className="w-4 h-4" />
                      <span className="text-xs font-medium">Nationalities</span>
                    </div>
                    <p className="text-sm font-semibold">{match.nationalities.join(', ')}</p>
                  </div>
                )}
                
                {match.date_of_birth_text && (
                  <div>
                    <div className="flex items-center gap-1 text-gray-600 mb-1">
                      <Calendar className="w-4 h-4" />
                      <span className="text-xs font-medium">Date of Birth</span>
                    </div>
                    <p className="text-sm font-semibold">{match.date_of_birth_text}</p>
                  </div>
                )}
                
                {match.program && (
                  <div>
                    <div className="flex items-center gap-1 text-gray-600 mb-1">
                      <Hash className="w-4 h-4" />
                      <span className="text-xs font-medium">Program</span>
                    </div>
                    <p className="text-sm font-semibold">{match.program}</p>
                  </div>
                )}
                
                {match.date_listed && (
                  <div>
                    <div className="flex items-center gap-1 text-gray-600 mb-1">
                      <Calendar className="w-4 h-4" />
                      <span className="text-xs font-medium">Date Listed</span>
                    </div>
                    <p className="text-sm font-semibold">{match.date_listed}</p>
                  </div>
                )}
              </div>

              {match.aliases && match.aliases.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-600 mb-2">Known Aliases:</p>
                  <div className="flex flex-wrap gap-2">
                    {match.aliases.map((alias: string, i: number) => (
                      <span key={i} className="bg-gray-100 px-3 py-1 rounded-full text-sm">
                        {alias}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {match.remarks && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-gray-600 mb-1">Additional Information:</p>
                  <p className="text-sm text-gray-700">{match.remarks}</p>
                </div>
              )}
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
              <p className="text-green-700">The entity "{searchTerm}" did not match any sanctions lists.</p>
            </div>
          </div>
        </div>
      )}

      {searchHistory.length > 0 && (
        <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
          <h3 className="font-bold text-lg mb-4">Search History</h3>
          <div className="space-y-2">
            {searchHistory.map((item, idx) => (
              <div key={idx} className="flex justify-between items-center py-2 border-b last:border-0">
                <div>
                  <span className="font-medium">{item.name}</span>
                  <span className="text-xs text-gray-500 ml-2">({item.type})</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {item.matchCount} match(es)
                  </span>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${
                    item.status === 'match' ? 'bg-red-100 text-red-700' :
                    item.status === 'potential_match' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {item.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

export default ScreeningPage;
