import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Lock, Unlock, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { decryptDocument } from '../services/api';

interface DecryptPanelProps {
  sessionId: string;
}

export const DecryptPanel: React.FC<DecryptPanelProps> = ({ sessionId }) => {
  const [password, setPassword] = useState('');
  const [decrypting, setDecrypting] = useState(false);
  const [decryptedText, setDecryptedText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDecrypt = async () => {
    if (!password) {
      setError('Please enter a decryption password');
      return;
    }

    setDecrypting(true);
    setError(null);

    try {
      const response = await decryptDocument(sessionId, password);
      setDecryptedText(response.original_text);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Decryption failed. Invalid password.');
      setDecryptedText(null);
    } finally {
      setDecrypting(false);
    }
  };

  const handleClearDecrypted = () => {
    setDecryptedText(null);
    setPassword('');
    setError(null);
  };

  return (
    <Card className="border-slate-200 rounded-xl shadow-sm">
      <CardHeader className="border-b border-slate-100">
        <CardTitle className="flex items-center space-x-2 text-lg font-semibold text-slate-900">
          <Lock className="w-5 h-5" />
          <span>Decrypt Original Content</span>
        </CardTitle>
        <CardDescription className="text-slate-500">
          Enter your account password to view the original document with PII
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6">
        {!decryptedText ? (
          <div className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">
                Account Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                onKeyPress={(e) => e.key === 'Enter' && handleDecrypt()}
                className="rounded-lg"
              />
            </div>

            <Button
              onClick={handleDecrypt}
              disabled={decrypting || !password}
              className="w-full flex items-center justify-center space-x-2 rounded-lg"
            >
              {decrypting ? (
                <>
                  <Lock className="w-4 h-4 animate-pulse" />
                  <span>Decrypting...</span>
                </>
              ) : (
                <>
                  <Unlock className="w-4 h-4" />
                  <span>Decrypt Document</span>
                </>
              )}
            </Button>

            {error && (
              <div className="flex items-start space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <h4 className="font-medium text-amber-800 mb-2 flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" />
                Security Notice
              </h4>
              <ul className="text-sm text-amber-700 space-y-1">
                <li>• Decrypted content contains sensitive PII</li>
                <li>• Only decrypt when absolutely necessary</li>
                <li>• Ensure you're in a secure environment</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span className="text-sm font-medium text-emerald-800">
                  Document decrypted successfully
                </span>
              </div>
              <Button variant="outline" size="sm" onClick={handleClearDecrypted} className="rounded-lg">
                Clear & Lock
              </Button>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                Original Document (Contains PII)
              </h3>
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-h-96 overflow-auto">
                <pre className="text-sm whitespace-pre-wrap text-slate-800">{decryptedText}</pre>
              </div>
            </div>

            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700 font-medium">
                ⚠️ This content contains unencrypted PII. Handle with care.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
