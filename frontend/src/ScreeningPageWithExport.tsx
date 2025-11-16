// Add this import at the top of your ScreeningPage.tsx
import { exportToExcel, exportToCSV, exportToPDF } from './exportUtils';
import { useState } from 'react';
import { Download, FileSpreadsheet, FileText, FileDown } from 'lucide-react';

// Add this component for the export menu
const ExportMenu = ({ result, entityName }: { result: any; entityName: string }) => {
  const [showMenu, setShowMenu] = useState(false);
  
  const exportData = {
    case_id: result.screening_id || result.case_id || 'N/A',
    search_term: entityName,
    entity_type: 'individual', // You can pass this as prop
    status: result.status,
    match_count: result.matches.length,
    matches: result.matches,
    timestamp: result.timestamp || new Date().toISOString(),
    user_email: result.user?.email
  };
  
  const handleExport = (type: 'excel' | 'csv' | 'pdf') => {
    setShowMenu(false);
    
    switch (type) {
      case 'excel':
        exportToExcel(exportData);
        break;
      case 'csv':
        exportToCSV(exportData);
        break;
      case 'pdf':
        exportToPDF(exportData);
        break;
    }
  };
  
  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg hover:bg-gray-50 transition border border-gray-300"
      >
        <Download className="w-4 h-4" />
        Export
      </button>
      
      {showMenu && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20">
            <button
              onClick={() => handleExport('pdf')}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 transition"
            >
              <FileText className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium">Export as PDF</span>
            </button>
            <button
              onClick={() => handleExport('excel')}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 transition"
            >
              <FileSpreadsheet className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium">Export as Excel</span>
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-3 transition"
            >
              <FileDown className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">Export as CSV</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
};

// Then in your existing ScreeningPage component, replace the export button (around line 280) with:
// <ExportMenu result={result} entityName={entityName} />
