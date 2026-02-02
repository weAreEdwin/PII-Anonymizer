import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Download, FileText, File, Code, FileType, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { exportDocument } from '../services/api';

interface ExportPanelProps {
  sessionId: string;
  filename: string;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({ sessionId, filename }) => {
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: 'pdf' | 'docx' | 'txt' | 'json') => {
    setExporting(format);
    setError(null);

    try {
      const blob = await exportDocument(sessionId, format);

      // Create download link
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Set filename with appropriate extension
      const baseFilename = filename.replace(/\.[^/.]+$/, '');
      if (format === 'json') {
        a.download = `${baseFilename}-pii-mapping.json`;
      } else {
        a.download = `${baseFilename}-anonymized.${format}`;
      }

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to export as ${format.toUpperCase()}`);
    } finally {
      setExporting(null);
    }
  };

  const exportOptions = [
    {
      format: 'pdf' as const,
      icon: FileText,
      title: 'Export as PDF',
      description: 'Anonymized document in PDF format',
      iconBg: 'bg-red-50',
      iconColor: 'text-red-600',
    },
    {
      format: 'docx' as const,
      icon: File,
      title: 'Export as DOCX',
      description: 'Anonymized document in Word format',
      iconBg: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      format: 'txt' as const,
      icon: FileType,
      title: 'Export as TXT',
      description: 'Anonymized document in plain text',
      iconBg: 'bg-slate-100',
      iconColor: 'text-slate-600',
    },
    {
      format: 'json' as const,
      icon: Code,
      title: 'Export PII Mapping',
      description: 'PII mapping data in JSON format',
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      variant: 'outline' as const,
    },
  ];

  return (
    <Card className="border-slate-200 rounded-xl shadow-sm">
      <CardHeader className="border-b border-slate-100">
        <CardTitle className="text-lg font-semibold text-slate-900">Export Options</CardTitle>
        <CardDescription className="text-slate-500">
          Download the anonymized document or PII mapping in various formats
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6">
        <div className="space-y-3">
          {exportOptions.map((option) => (
            <div
              key={option.format}
              className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className={`flex items-center justify-center w-11 h-11 ${option.iconBg} rounded-lg`}>
                  <option.icon className={`w-5 h-5 ${option.iconColor}`} />
                </div>
                <div>
                  <h3 className="font-medium text-slate-900">{option.title}</h3>
                  <p className="text-sm text-slate-500">{option.description}</p>
                </div>
              </div>
              <Button
                onClick={() => handleExport(option.format)}
                disabled={exporting !== null}
                variant={option.variant || 'default'}
                className="rounded-lg"
              >
                {exporting === option.format ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </>
                )}
              </Button>
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-lg">
          <h4 className="font-medium text-slate-700 mb-2">Export Information</h4>
          <ul className="text-sm text-slate-500 space-y-1">
            <li>• All exports contain only anonymized data (no original PII)</li>
            <li>• PDF, DOCX, and TXT maintain document content</li>
            <li>• JSON mapping shows placeholder-to-type relationships</li>
            <li>• Original values remain encrypted in the database</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
