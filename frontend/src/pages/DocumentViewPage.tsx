import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Shield, Lock } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { SplitView } from '../components/SplitView';
import { PiiLegend } from '../components/PiiLegend';
import { ExportPanel } from '../components/ExportPanel';
import { DecryptPanel } from '../components/DecryptPanel';
import { getDocumentSession } from '../services/api';

interface PiiMapping {
  id: number;
  original_value: string;
  placeholder: string;
  pii_type: string;
  confidence_score: number;
}

interface DocumentSession {
  session_id: string;
  filename: string;
  upload_timestamp: string;
  document_text: string;
  anonymized_text: string;
  pii_mappings: PiiMapping[];
}

export const DocumentViewPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<DocumentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'view' | 'export' | 'decrypt'>('view');

  useEffect(() => {
    const fetchSession = async () => {
      if (!sessionId) return;

      try {
        setLoading(true);
        const data = await getDocumentSession(sessionId);
        setSession(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load document session');
      } finally {
        setLoading(false);
      }
    };

    fetchSession();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-slate-300 border-t-slate-900 mx-auto"></div>
          <p className="mt-4 text-slate-500">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="w-full max-w-md border-slate-200 rounded-xl">
          <CardHeader>
            <CardTitle className="text-red-600">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">{error || 'Document not found'}</p>
            <Button onClick={() => navigate('/dashboard')} className="mt-4 rounded-lg">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                className="rounded-lg"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">{session.filename}</h1>
                <p className="text-sm text-slate-400">
                  Uploaded {new Date(session.upload_timestamp).toLocaleString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <p className="text-sm font-medium text-slate-700">
                  {session.pii_mappings.length} PII entities
                </p>
                <p className="text-xs text-slate-400">Successfully anonymized</p>
              </div>
              <div className="flex items-center justify-center w-10 h-10 bg-emerald-50 rounded-lg">
                <Shield className="w-5 h-5 text-emerald-600" />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-6">
        {/* Tab Navigation */}
        <div className="mb-6 flex space-x-1 bg-slate-100 p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('view')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'view'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
              }`}
          >
            <Shield className="w-4 h-4 inline mr-2" />
            View Document
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'export'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
              }`}
          >
            <Download className="w-4 h-4 inline mr-2" />
            Export
          </button>
          <button
            onClick={() => setActiveTab('decrypt')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${activeTab === 'decrypt'
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
              }`}
          >
            <Lock className="w-4 h-4 inline mr-2" />
            Decrypt
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'view' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <SplitView
                anonymizedText={session.anonymized_text}
                piiMappings={session.pii_mappings}
              />
            </div>
            <div>
              <PiiLegend piiMappings={session.pii_mappings} />
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div className="max-w-3xl mx-auto">
            <ExportPanel sessionId={session.session_id} filename={session.filename} />
          </div>
        )}

        {activeTab === 'decrypt' && (
          <div className="max-w-3xl mx-auto">
            <DecryptPanel sessionId={session.session_id} />
          </div>
        )}
      </main>
    </div>
  );
};
