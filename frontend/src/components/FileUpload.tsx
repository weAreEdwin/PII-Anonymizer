import React, { useState, useCallback } from 'react';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { uploadDocument } from '../services/api';

interface FileUploadProps {
  onUploadSuccess: (sessionId: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return 'Invalid file type. Please upload PDF, DOCX, or TXT files only.';
    }

    if (file.size > maxSize) {
      return 'File size exceeds 10MB limit.';
    }

    return null;
  };

  const handleFileSelect = useCallback((file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setError(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError(null);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const response = await uploadDocument(selectedFile, (progress) => {
        setUploadProgress(progress);
      });

      // Success - notify parent component
      onUploadSuccess(response.session_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document. Please try again.');
      setIsUploading(false);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.includes('pdf')) return '📄';
    if (file.type.includes('word')) return '📘';
    if (file.type.includes('text')) return '📝';
    return '📎';
  };

  return (
    <div className="w-full">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center transition-all
          ${isDragging ? 'border-slate-400 bg-slate-100' : 'border-slate-200 bg-slate-50'}
          ${selectedFile ? 'border-emerald-400 bg-emerald-50' : ''}
        `}
      >
        {!selectedFile ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${isDragging ? 'bg-slate-200' : 'bg-white border border-slate-200'}`}>
                <Upload className={`w-6 h-6 ${isDragging ? 'text-slate-600' : 'text-slate-400'}`} />
              </div>
            </div>
            <div>
              <p className="text-base font-medium text-slate-700">
                Drag and drop your file here
              </p>
              <p className="text-sm text-slate-400 mt-1">or</p>
            </div>
            <div>
              <label htmlFor="file-input">
                <Button type="button" variant="outline" asChild className="rounded-lg">
                  <span className="cursor-pointer">Browse Files</span>
                </Button>
              </label>
              <input
                id="file-input"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleInputChange}
                className="hidden"
              />
            </div>
            <p className="text-xs text-slate-400">
              Supported: PDF, DOCX, TXT (max 10MB)
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-3">
              <span className="text-4xl">{getFileIcon(selectedFile)}</span>
              <div className="text-left">
                <p className="font-medium text-slate-800">{selectedFile.name}</p>
                <p className="text-sm text-slate-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              {!isUploading && (
                <button
                  onClick={handleRemoveFile}
                  className="ml-4 p-1.5 hover:bg-slate-200 rounded-lg transition-colors"
                  aria-label="Remove file"
                >
                  <X className="w-4 h-4 text-slate-500" />
                </button>
              )}
            </div>

            {isUploading && (
              <div className="space-y-2">
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-slate-900 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-sm text-slate-500">
                  Uploading... {uploadProgress}%
                </p>
              </div>
            )}

            {!isUploading && (
              <Button
                onClick={handleUpload}
                className="w-full rounded-lg"
                disabled={isUploading}
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload and Process
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Loading Indicator */}
      {isUploading && (
        <div className="mt-4 flex items-center justify-center space-x-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Processing your document...</span>
        </div>
      )}
    </div>
  );
};
