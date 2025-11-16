import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { saveAs } from 'file-saver';

interface Match {
  entity_name: string;
  entity_type: string;
  list_source: string;
  program: string;
  nationalities: string[];
  combined_score: number;
  is_pep?: boolean;
  pep_level?: string;
  position?: string;
  jurisdiction?: string;
  risk_assessment?: {
    level: string;
    score: number;
  };
  aliases?: string[];
  remarks?: string;
}

interface ExportData {
  case_id: string;
  search_term: string;
  entity_type: string;
  status: string;
  match_count: number;
  matches: Match[];
  timestamp: string;
  user_email?: string;
}

// Export to Excel
export const exportToExcel = (data: ExportData) => {
  const wb = XLSX.utils.book_new();
  
  // Summary Sheet
  const summaryData = [
    ['ComplianceAI Pro - Screening Report'],
    [],
    ['Case ID', data.case_id],
    ['Search Term', data.search_term],
    ['Entity Type', data.entity_type],
    ['Status', data.status.toUpperCase()],
    ['Total Matches', data.match_count],
    ['Date & Time', new Date(data.timestamp).toLocaleString()],
    ['User', data.user_email || 'Anonymous'],
    [],
  ];
  
  const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
  
  // Set column widths
  summaryWs['!cols'] = [{ wch: 20 }, { wch: 50 }];
  
  XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary');
  
  // Matches Sheet
  if (data.matches.length > 0) {
    const matchesData = data.matches.map((match, idx) => ({
      '#': idx + 1,
      'Name': match.entity_name,
      'Type': match.entity_type,
      'Source': match.list_source,
      'Program': match.program,
      'Match Score': `${(match.combined_score * 100).toFixed(1)}%`,
      'Risk Level': match.risk_assessment?.level || 'N/A',
      'Risk Score': match.risk_assessment?.score || 'N/A',
      'PEP': match.is_pep ? 'Yes' : 'No',
      'PEP Level': match.pep_level || 'N/A',
      'Position': match.position || 'N/A',
      'Jurisdiction': match.jurisdiction || 'N/A',
      'Nationalities': match.nationalities?.join(', ') || 'N/A',
      'Aliases': match.aliases?.slice(0, 5).join(', ') || 'N/A'
    }));
    
    const matchesWs = XLSX.utils.json_to_sheet(matchesData);
    
    // Set column widths
    matchesWs['!cols'] = [
      { wch: 5 }, { wch: 40 }, { wch: 12 }, { wch: 15 }, 
      { wch: 30 }, { wch: 12 }, { wch: 12 }, { wch: 12 },
      { wch: 8 }, { wch: 15 }, { wch: 30 }, { wch: 20 },
      { wch: 20 }, { wch: 40 }
    ];
    
    XLSX.utils.book_append_sheet(wb, matchesWs, 'Matches');
  }
  
  // Export
  const fileName = `Screening_${data.case_id}_${Date.now()}.xlsx`;
  XLSX.writeFile(wb, fileName);
};

// Export to CSV
export const exportToCSV = (data: ExportData) => {
  const csvRows = [];
  
  // Header
  csvRows.push('ComplianceAI Pro - Screening Report');
  csvRows.push('');
  csvRows.push(`Case ID,${data.case_id}`);
  csvRows.push(`Search Term,${data.search_term}`);
  csvRows.push(`Entity Type,${data.entity_type}`);
  csvRows.push(`Status,${data.status.toUpperCase()}`);
  csvRows.push(`Total Matches,${data.match_count}`);
  csvRows.push(`Date & Time,${new Date(data.timestamp).toLocaleString()}`);
  csvRows.push(`User,${data.user_email || 'Anonymous'}`);
  csvRows.push('');
  csvRows.push('Detailed Matches:');
  csvRows.push('');
  
  // Column headers
  csvRows.push('#,Name,Type,Source,Program,Match Score,Risk Level,Risk Score,PEP,PEP Level,Position,Nationalities');
  
  // Data rows
  data.matches.forEach((match, idx) => {
    const row = [
      idx + 1,
      `"${match.entity_name.replace(/"/g, '""')}"`,
      match.entity_type,
      match.list_source,
      `"${match.program.replace(/"/g, '""')}"`,
      `${(match.combined_score * 100).toFixed(1)}%`,
      match.risk_assessment?.level || 'N/A',
      match.risk_assessment?.score || 'N/A',
      match.is_pep ? 'Yes' : 'No',
      match.pep_level || 'N/A',
      `"${(match.position || 'N/A').replace(/"/g, '""')}"`,
      `"${match.nationalities?.join(', ') || 'N/A'}"`
    ];
    csvRows.push(row.join(','));
  });
  
  const csvContent = csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  saveAs(blob, `Screening_${data.case_id}_${Date.now()}.csv`);
};

// Export to PDF
export const exportToPDF = async (data: ExportData) => {
  const doc = new jsPDF();
  
  // Try to add logo
  try {
    const img = new Image();
    img.src = '/logo.png';
    
    await new Promise((resolve, reject) => {
      img.onload = () => {
        try {
          doc.addImage(img, 'PNG', 14, 10, 25, 25);
          resolve(true);
        } catch (e) {
          console.warn('Could not add logo to PDF:', e);
          resolve(false);
        }
      };
      img.onerror = () => {
        console.warn('Logo not found');
        resolve(false);
      };
    });
  } catch (e) {
    console.warn('Logo loading error:', e);
  }
  
  // Header
  doc.setFontSize(24);
  doc.setTextColor(220, 38, 38); // Red color matching your logo
  doc.text('ComplianceAI Pro', 45, 20);
  
  doc.setFontSize(14);
  doc.setTextColor(100, 100, 100);
  doc.text('Sanctions & PEP Screening Report', 45, 28);
  
  // Add decorative line
  doc.setLineWidth(0.8);
  doc.setDrawColor(220, 38, 38);
  doc.line(14, 38, 196, 38);
  
  // Summary section
  let yPos = 50;
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(0, 0, 0);
  doc.text('Screening Summary', 14, yPos);
  
  yPos += 10;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  
  const summaryData = [
    ['Case ID:', data.case_id],
    ['Search Term:', data.search_term],
    ['Entity Type:', data.entity_type],
    ['Status:', data.status.toUpperCase().replace('_', ' ')],
    ['Total Matches:', data.match_count.toString()],
    ['Date & Time:', new Date(data.timestamp).toLocaleString()],
    ['User:', data.user_email || 'Anonymous']
  ];
  
  summaryData.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.text(label, 14, yPos);
    doc.setFont('helvetica', 'normal');
    
    // Wrap long text
    const maxWidth = 120;
    const lines = doc.splitTextToSize(value, maxWidth);
    doc.text(lines, 55, yPos);
    yPos += 6 * lines.length;
  });
  
  // Status badge
  yPos += 8;
  const statusColor = 
    data.status === 'match' ? [220, 38, 38] : 
    data.status === 'potential_match' ? [234, 179, 8] : 
    [34, 197, 94];
  
  doc.setFillColor(statusColor[0], statusColor[1], statusColor[2]);
  doc.roundedRect(14, yPos - 6, 60, 10, 2, 2, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.text(data.status.replace('_', ' ').toUpperCase(), 17, yPos);
  doc.setTextColor(0, 0, 0);
  
  // Matches table
  if (data.matches.length > 0) {
    yPos += 15;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(14);
    doc.text('Match Details', 14, yPos);
    
    yPos += 8;
    
    const tableData = data.matches.map((match, idx) => [
      (idx + 1).toString(),
      match.entity_name.substring(0, 40) + (match.entity_name.length > 40 ? '...' : ''),
      match.list_source,
      `${(match.combined_score * 100).toFixed(1)}%`,
      match.risk_assessment?.level || 'N/A',
      match.is_pep ? 'Yes' : 'No'
    ]);
    
    autoTable(doc, {
      startY: yPos,
      head: [['#', 'Name', 'Source', 'Score', 'Risk', 'PEP']],
      body: tableData,
      theme: 'grid',
      headStyles: { 
        fillColor: [220, 38, 38],
        textColor: 255,
        fontStyle: 'bold',
        fontSize: 10
      },
      alternateRowStyles: { fillColor: [252, 252, 252] },
      margin: { left: 14, right: 14 },
      styles: { fontSize: 9, cellPadding: 3 },
      columnStyles: {
        0: { cellWidth: 10 },
        1: { cellWidth: 70 },
        2: { cellWidth: 30 },
        3: { cellWidth: 20 },
        4: { cellWidth: 25 },
        5: { cellWidth: 15 }
      }
    });
    
    // Detailed match info on separate pages
    data.matches.forEach((match, idx) => {
      doc.addPage();
      
      // Logo on each page
      try {
        const img = new Image();
        img.src = '/logo.png';
        doc.addImage(img, 'PNG', 14, 10, 20, 20);
      } catch (e) {
        // Skip if logo fails
      }
      
      // Match header
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(220, 38, 38);
      doc.text(`Match #${idx + 1}`, 40, 20);
      
      doc.setFontSize(12);
      doc.setTextColor(0, 0, 0);
      const nameLines = doc.splitTextToSize(match.entity_name, 150);
      doc.text(nameLines, 14, 32);
      
      // Match details
      yPos = 45 + (nameLines.length * 5);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      
      const detailsData = [
        ['Entity Type:', match.entity_type],
        ['Source:', match.list_source],
        ['Program:', match.program],
        ['Match Score:', `${(match.combined_score * 100).toFixed(1)}%`],
        ['Risk Level:', match.risk_assessment?.level || 'N/A'],
        ['Risk Score:', match.risk_assessment?.score?.toString() || 'N/A'],
        ['Is PEP:', match.is_pep ? 'Yes' : 'No'],
      ];
      
      if (match.is_pep) {
        detailsData.push(
          ['PEP Level:', match.pep_level || 'N/A'],
          ['Position:', match.position || 'N/A'],
          ['Jurisdiction:', match.jurisdiction || 'N/A']
        );
      }
      
      detailsData.push(['Nationalities:', match.nationalities?.join(', ') || 'N/A']);
      
      if (match.aliases && match.aliases.length > 0) {
        detailsData.push(['Aliases:', match.aliases.slice(0, 5).join(', ')]);
      }
      
      if (match.remarks) {
        detailsData.push(['Remarks:', match.remarks]);
      }
      
      detailsData.forEach(([label, value]) => {
        doc.setFont('helvetica', 'bold');
        doc.text(label, 14, yPos);
        doc.setFont('helvetica', 'normal');
        
        const valueLines = doc.splitTextToSize(value, 130);
        doc.text(valueLines, 60, yPos);
        yPos += 6 * valueLines.length;
        
        if (yPos > 270) {
          doc.addPage();
          yPos = 20;
        }
      });
    });
  }
  
  // Footer on all pages
  const pageCount = doc.getNumberOfPages();
  doc.setFontSize(8);
  doc.setTextColor(128, 128, 128);
  
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.text(
      `ComplianceAI Pro © ${new Date().getFullYear()} - Confidential`,
      14,
      doc.internal.pageSize.height - 15
    );
    doc.text(
      `Generated: ${new Date().toLocaleString()}`,
      105,
      doc.internal.pageSize.height - 15,
      { align: 'center' }
    );
    doc.text(
      `Page ${i} of ${pageCount}`,
      doc.internal.pageSize.width - 14,
      doc.internal.pageSize.height - 15,
      { align: 'right' }
    );
  }
  
  // Save
  doc.save(`ComplianceAI_Screening_${data.case_id}_${Date.now()}.pdf`);
};