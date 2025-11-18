import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Building, 
  AlertTriangle, 
  Info, 
  Calendar, 
  MapPin, 
  Globe, 
  FileText,
  Hash,
  Shield,
  ShieldAlert
} from 'lucide-react';

const MatchDetails = ({ match, riskLevel }) => {
  if (!match) return null;

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.9) return 'bg-green-100 text-green-800';
    if (confidence >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  const getEntityIcon = (type) => {
    return type === 'entity' ? 
      <Building className="h-4 w-4" /> : 
      <User className="h-4 w-4" />;
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {getEntityIcon(match.type)}
            {match.name}
          </CardTitle>
          <div className="flex gap-2">
            <Badge className={getConfidenceColor(match.confidence)}>
              Confidence: {getConfidenceLabel(match.confidence)} ({formatConfidence(match.confidence)})
            </Badge>
            <Badge className={getRiskColor(riskLevel)}>
              {riskLevel?.toUpperCase() || 'LOW'} RISK
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">List Type:</span>
              <Badge variant="outline">{match.list_type}</Badge>
            </div>
            
            <div className="flex items-center gap-2">
              <Hash className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Program:</span>
              <span className="text-sm">{match.program}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Nationalities:</span>
              <span className="text-sm">{match.nationalities}</span>
            </div>
            
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-gray-500 mt-0.5" />
              <div>
                <span className="text-sm font-medium">Aliases:</span>
                <p className="text-sm mt-1">{match.aliases}</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Date of Birth:</span>
              <span className="text-sm">{match.date_of_birth}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Place of Birth:</span>
              <span className="text-sm">{match.place_of_birth}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Jurisdiction:</span>
              <span className="text-sm">{match.jurisdiction}</span>
            </div>
            
            <div className="flex items-center gap-2">
              {match.is_pep ? (
                <ShieldAlert className="h-4 w-4 text-amber-500" />
              ) : (
                <Shield className="h-4 w-4 text-gray-500" />
              )}
              <span className="text-sm font-medium">Status:</span>
              <Badge variant={match.is_pep ? "default" : "outline"}>
                {match.is_pep ? "PEP" : "Sanctions"}
              </Badge>
            </div>
          </div>
        </div>
        
        {match.remarks && (
          <>
            <Separator />
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-gray-500 mt-0.5" />
              <div>
                <span className="text-sm font-medium">Remarks:</span>
                <p className="text-sm mt-1">{match.remarks}</p>
              </div>
            </div>
          </>
        )}
        
        <Separator />
        
        <div className="bg-gray-50 p-3 rounded-md">
          <span className="text-sm font-medium">Full Details:</span>
          <p className="text-sm mt-1 whitespace-pre-wrap">{match.details}</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default MatchDetails;
