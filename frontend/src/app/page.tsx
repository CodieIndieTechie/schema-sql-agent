'use client';

import { useState, useEffect, useRef } from 'react';
import { GoogleAuth } from '../components/auth/GoogleAuth';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface User {
  email: string;
  name: string;
  picture?: string;
  database_name: string;
}

interface TableData {
  columns: string[];
  data: any[][];
}

export default function MultiTenantSQLAgent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('jwt_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: getAuthHeaders()
      });
      
      if (response.status === 200) {
        setCurrentUser(response.data);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('jwt_token');
    }
  };

  const loadUserData = async () => {
    if (!currentUser) return;

    try {
      const response = await axios.get(`${API_BASE_URL}/user/tables`, {
        headers: getAuthHeaders()
      });
      
      // The tables endpoint returns table names, not table data
      // Table data (tableData) should only be set when query results are available
      console.log('Available tables:', response.data.tables);
    } catch (error) {
      console.error('Failed to load user data:', error);
    }
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadUserData();
    }
  }, [currentUser]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendQuery = async () => {
    if (!inputValue.trim() || !currentUser) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputValue('');

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: inputValue.trim()
      }, { headers: getAuthHeaders() });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response,
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      if (response.data.table_data) {
        setTableData(response.data.table_data);
      }
    } catch (error) {
      console.error('Query failed:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error processing your query. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!files || files.length === 0 || !currentUser) return;

    setIsUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-files`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getAuthHeaders()
        }
      });

      setUploadStatus(`✅ Successfully uploaded ${files.length} file(s)`);
      setFiles(null);
      await loadUserData();
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('❌ Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  if (!currentUser) {
    return <GoogleAuth />;
  }

  return (
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 elevation-1 sticky top-0 z-10">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              </div>
              <div>
                <h1 className="text-title-large text-primary font-semibold">SQL Agent</h1>
                <p className="text-label-small text-secondary">Natural Language Database Query</p>
              </div>
            </div>
            <GoogleAuth />
          </div>
        </div>
      </header>

      <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
        {/* Mobile File Upload */}
        <div className="md:hidden mb-6">
          <div className="card elevation-2">
            <div className="border-b border-gray-100 p-4">
              <h3 className="text-title-small text-primary font-semibold">Upload Files</h3>
              <p className="text-body-small text-secondary">Add CSV or Excel files to your database</p>
            </div>
            <div className="p-4 space-y-4">
              <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-blue-300 transition-colors">
                <input
                  type="file"
                  multiple
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setFiles(e.target.files)}
                  className="hidden"
                  id="mobile-file-upload"
                />
                <label htmlFor="mobile-file-upload" className="cursor-pointer">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mx-auto mb-2">
                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <p className="text-body-small text-primary font-medium">Choose files</p>
                  <p className="text-label-small text-secondary">or drag and drop</p>
                </label>
              </div>

              {files && files.length > 0 && (
                <div className="space-y-2">
                  <p className="text-label-medium text-secondary">Selected files:</p>
                  {Array.from(files).slice(0, 2).map((file, index) => (
                    <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
                      <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="text-label-small text-gray-600 truncate">{file.name}</span>
                    </div>
                  ))}
                  {files.length > 2 && (
                    <p className="text-label-small text-secondary text-center">+{files.length - 2} more files</p>
                  )}
                </div>
              )}

              <button
                onClick={handleFileUpload}
                disabled={!files || files.length === 0 || isUploading}
                className="btn-filled w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Uploading...
                  </>
                ) : (
                  'Upload Files'
                )}
              </button>

              {uploadStatus && (
                <div className={`p-3 rounded-lg text-body-small ${
                  uploadStatus.includes('✅') 
                    ? 'bg-green-50 text-green-800 border border-green-200' 
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  {uploadStatus}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-6 h-[calc(100vh-140px)]">
          {/* Left Sidebar - File Upload */}
          <div className="w-80 flex-shrink-0 hidden md:block">
            <div className="card elevation-2 h-full">
              <div className="border-b border-gray-100 p-4">
                <h3 className="text-title-small text-primary font-semibold">Upload Files</h3>
                <p className="text-body-small text-secondary">Add CSV or Excel files</p>
              </div>
              <div className="p-4 space-y-4">
                <div className="border-2 border-dashed border-gray-200 rounded-lg p-4 text-center hover:border-blue-300 transition-colors">
                  <input
                    type="file"
                    multiple
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => setFiles(e.target.files)}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mx-auto mb-2">
                      <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-body-small text-primary font-medium">Choose files</p>
                    <p className="text-label-small text-secondary">or drag and drop</p>
                  </label>
                </div>

                {files && files.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-label-medium text-secondary">Selected:</p>
                    {Array.from(files).slice(0, 3).map((file, index) => (
                      <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded-lg">
                        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-label-small text-gray-600 truncate">{file.name}</span>
                      </div>
                    ))}
                    {files.length > 3 && (
                      <p className="text-label-small text-secondary text-center">+{files.length - 3} more files</p>
                    )}
                  </div>
                )}

                <button
                  onClick={handleFileUpload}
                  disabled={!files || files.length === 0 || isUploading}
                  className="btn-filled w-full disabled:opacity-50 disabled:cursor-not-allowed text-sm py-2"
                >
                  {isUploading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    'Upload Files'
                  )}
                </button>

                {uploadStatus && (
                  <div className={`p-2 rounded-lg text-label-small ${
                    uploadStatus.includes('✅') 
                      ? 'bg-green-50 text-green-800 border border-green-200' 
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {uploadStatus}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Main Chat Section */}
          <div className="flex-1 min-w-0">
            <div className="card elevation-2 h-full flex flex-col">
              {/* Chat Header */}
              <div className="border-b border-gray-100 p-4">
                <h2 className="text-title-medium text-primary font-semibold">Chat with Your Data</h2>
                <p className="text-body-small text-secondary">Ask questions about your database in natural language</p>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                    <h3 className="text-title-small text-primary font-medium mb-2">Start a conversation</h3>
                    <p className="text-body-small text-secondary mb-4">Try asking questions like:</p>
                    <div className="space-y-2 max-w-md mx-auto">
                      <div className="bg-blue-50 p-3 rounded-lg text-left">
                        <p className="text-body-small text-blue-800">"Show me all customers from California"</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg text-left">
                        <p className="text-body-small text-green-800">"What's the total sales for this month?"</p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded-lg text-left">
                        <p className="text-body-small text-purple-800">"Count the number of orders by status"</p>
                      </div>
                    </div>
                  </div>
                )}

                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`${message.isUser ? 'max-w-xs lg:max-w-md' : 'max-w-2xl'} px-4 py-3 rounded-2xl ${
                      message.isUser 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-50 text-gray-900 border border-gray-200'
                    }`}>
                      <p className="text-body-medium whitespace-pre-wrap break-words">{message.text}</p>
                      <p className={`text-label-small mt-1 ${
                        message.isUser ? 'text-blue-100' : 'text-gray-400'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 max-w-xs">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <span className="text-body-small text-secondary">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-100 p-4">
                <div className="flex space-x-3">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask a question about your data..."
                    className="input-outlined flex-1 min-h-[48px] max-h-32 resize-none"
                    rows={1}
                    disabled={isLoading}
                  />
                  <button
                    onClick={sendQuery}
                    disabled={isLoading || !inputValue.trim()}
                    className="btn-filled px-4 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
