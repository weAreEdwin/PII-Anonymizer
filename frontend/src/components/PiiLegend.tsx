import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Copy, Check, Download } from 'lucide-react';
import { Button } from './ui/button';

interface PiiMapping {
  id: number;
  original_value: string;
  placeholder: string;
  pii_type: string;
  confidence_score: number;
}

interface PiiLegendProps {
  piiMappings: PiiMapping[];
}

export const PiiLegend: React.FC<PiiLegendProps> = ({ piiMappings }) => {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const handleCopy = async (mapping: PiiMapping) => {
    await navigator.clipboard.writeText(mapping.placeholder);
    setCopiedId(mapping.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownloadJSON = () => {
    const data = piiMappings.map((m) => ({
      type: m.pii_type,
      placeholder: m.placeholder,
      confidence: m.confidence_score,
    }));

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pii-mappings-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPiiTypeStyle = (piiType: string): string => {
    const styleMap: Record<string, string> = {
      PERSON: 'bg-blue-50 text-blue-700',
      EMAIL: 'bg-emerald-50 text-emerald-700',
      PHONE: 'bg-violet-50 text-violet-700',
      SSN: 'bg-red-50 text-red-700',
      CREDIT_CARD: 'bg-amber-50 text-amber-700',
      ADDRESS: 'bg-yellow-50 text-yellow-700',
      DATE: 'bg-pink-50 text-pink-700',
      ORG: 'bg-indigo-50 text-indigo-700',
    };
    return styleMap[piiType] || 'bg-slate-50 text-slate-700';
  };

  const groupedMappings = piiMappings.reduce((acc, mapping) => {
    if (!acc[mapping.pii_type]) {
      acc[mapping.pii_type] = [];
    }
    acc[mapping.pii_type].push(mapping);
    return acc;
  }, {} as Record<string, PiiMapping[]>);

  return (
    <Card className="border-slate-200 rounded-xl shadow-sm">
      <CardHeader className="border-b border-slate-100">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-slate-900">PII Detected</CardTitle>
          <Button variant="outline" size="sm" onClick={handleDownloadJSON} className="rounded-lg">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          {piiMappings.length} entities found
        </p>
      </CardHeader>
      <CardContent className="p-4">
        <div className="space-y-4 max-h-[400px] overflow-y-auto">
          {Object.entries(groupedMappings).map(([type, mappings]) => (
            <div key={type}>
              <div className="flex items-center space-x-2 mb-2">
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded-md ${getPiiTypeStyle(type)}`}>
                  {type}
                </span>
                <span className="text-xs text-slate-400">({mappings.length})</span>
              </div>
              <div className="space-y-1.5 ml-2">
                {mappings.map((mapping) => (
                  <div
                    key={mapping.id}
                    className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-mono text-slate-700 truncate">
                        {mapping.placeholder}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {(mapping.confidence_score * 100).toFixed(0)}% confidence
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(mapping)}
                      className="ml-2 flex-shrink-0"
                    >
                      {copiedId === mapping.id ? (
                        <Check className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-slate-400" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {piiMappings.length === 0 && (
          <div className="text-center py-8 text-slate-400">
            <p className="text-sm">No PII detected</p>
          </div>
        )}

        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <p className="text-xs text-slate-500">
            Original values are encrypted. Use the Decrypt tab to view with authentication.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
