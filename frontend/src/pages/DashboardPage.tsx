import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Upload, FileText, LogOut, Shield, Clock, Trash2 } from 'lucide-react';
import { FileUpload } from '../components/FileUpload';
import { uploadApi } from '../services/api';

interface SessionItem {
  session_id: string;
  original_filename: string;
  upload_timestamp: string;
  pii_count: number;
}

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalPiiCount, setTotalPiiCount] = useState(0);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await uploadApi.getSessions();
      setSessions(response.sessions || []);
      const total = (response.sessions || []).reduce((acc: number, s: SessionItem) => acc + (s.pii_count || 0), 0);
      setTotalPiiCount(total);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleUploadSuccess = useCallback((sessionId: string) => {
    navigate(`/document/${sessionId}`);
  }, [navigate]);

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await uploadApi.deleteSession(sessionId);
      fetchSessions();
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-9 h-9 bg-slate-900 rounded-lg">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">PII Anonymizer</h1>
                <p className="text-xs text-slate-500">Secure Document Processing</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-slate-700">{user?.username}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="rounded-lg"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-slate-900 mb-1">Welcome back, {user?.username}</h2>
          <p className="text-slate-500">Upload documents to detect and anonymize personal information</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
          {/* Stats Cards */}
          <Card className="border-slate-200 rounded-xl shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Documents Processed</CardTitle>
              <FileText className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold text-slate-900">{sessions.length}</div>
              <p className="text-xs text-slate-400 mt-1">All time</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200 rounded-xl shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">PII Detected</CardTitle>
              <Shield className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold text-slate-900">{totalPiiCount}</div>
              <p className="text-xs text-slate-400 mt-1">Total entities</p>
            </CardContent>
          </Card>

          <Card className="border-slate-200 rounded-xl shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Success Rate</CardTitle>
              <Upload className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-semibold text-slate-900">100%</div>
              <p className="text-xs text-slate-400 mt-1">Processing accuracy</p>
            </CardContent>
          </Card>
        </div>

        {/* Upload Section */}
        <Card className="border-slate-200 rounded-xl shadow-sm mb-8">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-900">Upload Document</CardTitle>
            <CardDescription className="text-slate-500">
              Upload PDF, DOCX, or TXT files to detect and anonymize personally identifiable information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </CardContent>
        </Card>

        {/* Recent Documents */}
        {sessions.length > 0 && (
          <Card className="border-slate-200 rounded-xl shadow-sm mb-8">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-slate-900">Recent Documents</CardTitle>
              <CardDescription className="text-slate-500">
                Click on a document to view details and export
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.session_id}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                    onClick={() => navigate(`/document/${session.session_id}`)}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-white rounded-lg border border-slate-200 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-slate-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{session.original_filename}</p>
                        <div className="flex items-center space-x-3 text-xs text-slate-400">
                          <span className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {new Date(session.upload_timestamp).toLocaleDateString()}
                          </span>
                          <span>{session.pii_count} PII entities</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(session.session_id);
                      }}
                      className="text-slate-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Card className="border-slate-200 rounded-xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-slate-900">How It Works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-7 h-7 bg-slate-900 text-white rounded-lg flex items-center justify-center text-sm font-medium">
                  1
                </div>
                <div>
                  <p className="font-medium text-slate-900">Upload Document</p>
                  <p className="text-sm text-slate-500">Select your PDF, DOCX, or TXT file</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-7 h-7 bg-slate-900 text-white rounded-lg flex items-center justify-center text-sm font-medium">
                  2
                </div>
                <div>
                  <p className="font-medium text-slate-900">Pattern Detection</p>
                  <p className="text-sm text-slate-500">Advanced algorithms identify all PII in your document</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-7 h-7 bg-slate-900 text-white rounded-lg flex items-center justify-center text-sm font-medium">
                  3
                </div>
                <div>
                  <p className="font-medium text-slate-900">Review & Export</p>
                  <p className="text-sm text-slate-500">View results and export the anonymized version</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 rounded-xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-slate-900">Supported PII Types</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                {[
                  'Names',
                  'Email Addresses',
                  'Phone Numbers',
                  'SSN',
                  'Credit Cards',
                  'Addresses',
                  'Dates of Birth',
                  'IP Addresses',
                ].map((type) => (
                  <div key={type} className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
                    <span className="text-sm text-slate-600">{type}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};
