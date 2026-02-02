/**
 * API Client for PII Anonymizer Backend
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Authentication
// ============================================================================

export interface RegisterData {
  username: string;
  email: string;
  password: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export const authApi = {
  register: async (data: RegisterData): Promise<UserResponse> => {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  login: async (data: LoginData): Promise<TokenResponse> => {
    const response = await api.post('/api/auth/login', data);
    return response.data;
  },

  getProfile: async (): Promise<UserResponse> => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// ============================================================================
// Document Upload & Sessions
// ============================================================================

export interface UploadResponse {
  session_id: string;
  filename: string;
  message: string;
  processing_time: number;
}

export interface SessionListItem {
  session_id: string;
  original_filename: string;
  upload_timestamp: string;
  last_accessed: string;
  export_count: number;
  pii_count: number;
}

export interface SessionDetail {
  session_id: string;
  filename: string;
  upload_timestamp: string;
  anonymized_text: string;
  pii_mappings: PIIMapping[];
  export_count: number;
  last_accessed: string;
}

export interface PIIMapping {
  original: string;
  placeholder: string;
  pii_type: string;
  confidence_score: number;
  detection_method: string;
}

export const uploadApi = {
  uploadDocument: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getSessions: async (): Promise<SessionListItem[]> => {
    const response = await api.get('/api/documents');
    return response.data;
  },

  getSession: async (sessionId: string): Promise<SessionDetail> => {
    const response = await api.get(`/api/document/${sessionId}`);
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/api/document/${sessionId}`);
  },
};

// ============================================================================
// Export
// ============================================================================

export type ExportFormat = 'pdf' | 'docx' | 'txt' | 'json';

export const exportApi = {
  exportDocument: async (sessionId: string, format: ExportFormat): Promise<Blob> => {
    const response = await api.get(`/api/export/${sessionId}/${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  downloadExport: (sessionId: string, format: ExportFormat, filename: string) => {
    const url = `${API_BASE_URL}/api/export/${sessionId}/${format}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  },
};

// ============================================================================
// Decrypt
// ============================================================================

export interface DecryptRequest {
  password: string;
}

export interface DecryptResponse {
  session_id: string;
  original_text: string;
  decrypted_at: string;
  message: string;
}

export interface DecryptPermission {
  session_id: string;
  can_decrypt: boolean;
  remaining_attempts: number;
  max_attempts: number;
  window_hours: number;
  last_decrypt_at: string | null;
  message: string;
}

export const decryptApi = {
  decryptDocument: async (
    sessionId: string,
    password: string
  ): Promise<DecryptResponse> => {
    const response = await api.post(`/api/decrypt/${sessionId}`, { password });
    return response.data;
  },

  checkPermission: async (sessionId: string): Promise<DecryptPermission> => {
    const response = await api.get(`/api/decrypt/${sessionId}/can-decrypt`);
    return response.data;
  },

  getAuditLog: async (sessionId: string): Promise<any> => {
    const response = await api.get(`/api/decrypt/${sessionId}/audit-log`);
    return response.data;
  },
};

// ============================================================================
// Chat
// ============================================================================

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  session_id: string;
  user_message: string;
  bot_response: string;
  contexts: string[];
  context_count: number;
}

export interface ChatHistoryResponse {
  session_id: string;
  message_count: number;
  messages: Array<{
    timestamp: string;
    user: string;
    bot: string;
  }>;
}

export interface SuggestionsResponse {
  session_id: string;
  suggestions: string[];
  pii_types_detected: string[];
}

export const chatApi = {
  sendMessage: async (
    sessionId: string,
    message: string
  ): Promise<ChatResponse> => {
    const response = await api.post(`/api/chat/${sessionId}`, { message });
    return response.data;
  },

  getHistory: async (sessionId: string): Promise<ChatHistoryResponse> => {
    const response = await api.get(`/api/chat/${sessionId}/history`);
    return response.data;
  },

  clearHistory: async (sessionId: string): Promise<void> => {
    await api.delete(`/api/chat/${sessionId}/clear`);
  },

  getSuggestions: async (sessionId: string): Promise<SuggestionsResponse> => {
    const response = await api.get(`/api/chat/${sessionId}/suggestions`);
    return response.data;
  },
};

// Standalone exports for direct imports
export const uploadDocument = uploadApi.uploadDocument;
export const exportDocument = exportApi.exportDocument;
export const sendChatMessage = chatApi.sendMessage;
export const decryptDocument = decryptApi.decryptDocument;
export const getDocumentSession = uploadApi.getSession;

export default api;


