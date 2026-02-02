import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface PiiMapping {
  id: number;
  original_value: string;
  placeholder: string;
  pii_type: string;
  confidence_score: number;
}

interface SplitViewProps {
  anonymizedText: string;
  piiMappings: PiiMapping[];
}

export const SplitView: React.FC<SplitViewProps> = ({
  anonymizedText,
  piiMappings,
}) => {
  const highlightPii = (text: string) => {
    if (!text) return text;

    let highlightedText = text;
    const sortedMappings = [...piiMappings].sort(
      (a, b) => b.placeholder.length - a.placeholder.length
    );

    sortedMappings.forEach((mapping) => {
      const regex = new RegExp(mapping.placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');

      const color = getPiiColor(mapping.pii_type);
      highlightedText = highlightedText.replace(
        regex,
        `<mark class="${color} px-1 py-0.5 rounded text-sm font-medium" title="${mapping.pii_type}">${mapping.placeholder}</mark>`
      );
    });

    return highlightedText;
  };

  const getPiiColor = (piiType: string): string => {
    const colorMap: Record<string, string> = {
      PERSON: 'bg-blue-100 text-blue-800',
      EMAIL: 'bg-emerald-100 text-emerald-800',
      PHONE: 'bg-violet-100 text-violet-800',
      SSN: 'bg-red-100 text-red-800',
      CREDIT_CARD: 'bg-amber-100 text-amber-800',
      ADDRESS: 'bg-yellow-100 text-yellow-800',
      DATE: 'bg-pink-100 text-pink-800',
      ORG: 'bg-indigo-100 text-indigo-800',
    };
    return colorMap[piiType] || 'bg-slate-100 text-slate-800';
  };

  return (
    <Card className="border-slate-200 rounded-xl shadow-sm">
      <CardHeader className="border-b border-slate-100">
        <CardTitle className="text-lg font-semibold text-slate-900">Anonymized Document</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
            <span className="text-sm font-medium text-slate-600">Safe to share</span>
          </div>
          <div
            className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm leading-relaxed text-slate-700 whitespace-pre-wrap overflow-auto max-h-[500px]"
            dangerouslySetInnerHTML={{
              __html: highlightPii(anonymizedText),
            }}
          />
        </div>
        <div className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <p className="text-xs text-slate-500">
            <strong className="text-slate-600">Note:</strong> Hover over highlighted placeholders to see the PII type.
            Original values are encrypted and can be accessed via the Decrypt tab with proper authentication.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
