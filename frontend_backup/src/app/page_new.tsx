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

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
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
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [chatSessions] = useState<ChatSession[]>([
    { id: '1', title: 'Sales Analysis Query', timestamp: new Date(Date.now() - 86400000) },
    { id: '2', title: 'Customer Demographics', timestamp: new Date(Date.now() - 172800000) },
    { id: '3', title: 'Revenue Breakdown', timestamp: new Date(Date.now() - 259200000) },
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      
      setCurrentUser(response.data);
      await fetchUserTables();
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('jwt_token');
    }
  };

  const fetchUserTables = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/user/tables`, {
        headers: getAuthHeaders()
      });
      
      if (response.data.tables && response.data.tables.length > 0) {
        const firstTable = response.data.tables[0];
        setTableData({
          columns: firstTable.columns,
          data: firstTable.data
        });
      }
    } catch (error) {
      console.error('Failed to fetch tables:', error);
    }
  };

  const handleAuth = (userData: any) => {
    setCurrentUser(userData);
    fetchUserTables();
  };

  const sendQuery = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: inputValue
      }, {
        headers: getAuthHeaders()
      });

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response || 'Query executed successfully',
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      if (response.data.table_data) {
        setTableData(response.data.table_data);
      }
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error processing your query. Please try again.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  const handleFileUpload = async () => {
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-files`, formData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus('✅ Files uploaded successfully! Data is now available in your database.');
      setFiles(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      setTimeout(() => {
        fetchUserTables();
      }, 1000);
    } catch (error: any) {
      setUploadStatus('❌ Upload failed. Please try again.');
    }

    setIsUploading(false);
  };

  const startNewChat = () => {
    setMessages([]);
    setInputValue('');
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <GoogleAuth onAuthSuccess={handleAuth} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarExpanded(!sidebarExpanded)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
            >
              <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">SQL Agent</h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="text-sm text-gray-600 hidden sm:block">
              {currentUser.database_name}
            </div>
            <div className="flex items-center space-x-2">
              {currentUser.picture && (
                <img 
                  src={currentUser.picture} 
                  alt={currentUser.name}
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-sm font-medium text-gray-700 hidden sm:block">
                {currentUser.name}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <div 
          className={`bg-gray-50 border-r border-gray-200 transition-all duration-200 ${
            sidebarExpanded ? 'w-64' : 'w-16'
          } hover:w-64 group`}
          onMouseEnter={() => setSidebarExpanded(true)}
          onMouseLeave={() => setSidebarExpanded(false)}
        >
          <div className="p-4 h-full">
            {/* New Chat Button */}
            <button
              onClick={startNewChat}
              className="w-full mb-6 p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-3"
            >
              <svg className="w-5 h-5 text-gray-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className={`text-sm font-medium text-gray-700 transition-opacity ${
                sidebarExpanded || 'group-hover:block' ? 'opacity-100' : 'opacity-0'
              }`}>
                New Chat
              </span>
            </button>

            {/* Recent Chats */}
            <div className="space-y-2">
              <h3 className={`text-xs font-medium text-gray-500 uppercase tracking-wide mb-3 transition-opacity ${
                sidebarExpanded || 'group-hover:block' ? 'opacity-100' : 'opacity-0'
              }`}>
                Recent
              </h3>
              {chatSessions.map((session) => (
                <button
                  key={session.id}
                  className="w-full p-2 rounded-lg hover:bg-white transition-colors flex items-center space-x-3 text-left"
                >
                  <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <div className={`transition-opacity ${
                    sidebarExpanded || 'group-hover:block' ? 'opacity-100' : 'opacity-0'
                  }`}>
                    <p className="text-sm text-gray-700 truncate">{session.title}</p>
                    <p className="text-xs text-gray-400">
                      {session.timestamp.toLocaleDateString()}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {/* Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6">
              {messages.length === 0 && (
                <div className="text-center py-12 max-w-2xl mx-auto">
                  <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-semibold text-gray-900 mb-3">
                    What can I help you with today?
                  </h2>
                  <p className="text-gray-600 mb-8">
                    Ask questions about your data in natural language
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-xl text-left hover:bg-gray-100 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-1">Data Analysis</h3>
                      <p className="text-sm text-gray-600">"Show me sales trends for the last quarter"</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-xl text-left hover:bg-gray-100 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-1">Customer Insights</h3>
                      <p className="text-sm text-gray-600">"Which customers have the highest lifetime value?"</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-xl text-left hover:bg-gray-100 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-1">Performance Metrics</h3>
                      <p className="text-sm text-gray-600">"Compare this month's revenue to last month"</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-xl text-left hover:bg-gray-100 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-1">Data Summary</h3>
                      <p className="text-sm text-gray-600">"Give me a summary of all my tables"</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="max-w-4xl mx-auto space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`${message.isUser ? 'max-w-xs lg:max-w-md' : 'max-w-3xl'} px-4 py-3 rounded-2xl ${
                      message.isUser 
                        ? 'bg-blue-500 text-white' 
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      <p className="text-sm whitespace-pre-wrap break-words">{message.text}</p>
                      <p className={`text-xs mt-2 ${
                        message.isUser ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-2xl px-4 py-3 max-w-xs">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                        <span className="text-sm text-gray-600">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-6">
              <div className="max-w-4xl mx-auto">
                {/* Upload Status */}
                {uploadStatus && (
                  <div className={`mb-4 p-3 rounded-lg text-sm ${
                    uploadStatus.includes('✅') 
                      ? 'bg-green-50 text-green-800 border border-green-200' 
                      : 'bg-red-50 text-red-800 border border-red-200'
                  }`}>
                    {uploadStatus}
                  </div>
                )}

                {/* Selected Files Preview */}
                {files && files.length > 0 && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium text-blue-800">
                        {files.length} file{files.length > 1 ? 's' : ''} selected
                      </p>
                      <button
                        onClick={() => {
                          setFiles(null);
                          if (fileInputRef.current) fileInputRef.current.value = '';
                        }}
                        className="text-blue-600 hover:text-blue-800 text-sm"
                      >
                        Clear
                      </button>
                    </div>
                    <div className="space-y-1">
                      {Array.from(files).slice(0, 3).map((file, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span className="text-sm text-blue-800 truncate max-w-xs">{file.name}</span>
                        </div>
                      ))}
                      {files.length > 3 && (
                        <p className="text-sm text-blue-600">+{files.length - 3} more files</p>
                      )}
                    </div>
                    <button
                      onClick={handleFileUpload}
                      disabled={isUploading}
                      className="mt-3 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUploading ? 'Uploading...' : 'Upload Files'}
                    </button>
                  </div>
                )}

                {/* Chat Input */}
                <div className="relative">
                  <div className="flex items-end space-x-3 bg-gray-50 rounded-3xl p-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) => setFiles(e.target.files)}
                      className="hidden"
                    />
                    
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex-shrink-0 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-full transition-colors"
                      title="Attach files"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                      </svg>
                    </button>

                    <textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyDown={handleKeyPress}
                      placeholder="Ask anything about your data..."
                      className="flex-1 bg-transparent border-none outline-none resize-none text-gray-900 placeholder-gray-500 py-3 px-2 min-h-[20px] max-h-32"
                      rows={1}
                      disabled={isLoading}
                    />

                    <button
                      onClick={sendQuery}
                      disabled={isLoading || !inputValue.trim()}
                      className="flex-shrink-0 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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

          {/* Right Data Preview Sidebar */}
          {tableData && (
            <div className="w-80 bg-gray-50 border-l border-gray-200 hidden xl:block">
              <div className="p-4 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Preview</h3>
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs">
                      <thead className="bg-gray-50">
                        <tr>
                          {tableData.columns.slice(0, 3).map((column, index) => (
                            <th key={index} className="px-3 py-2 text-left font-medium text-gray-900 truncate">
                              {column}
                            </th>
                          ))}
                          {tableData.columns.length > 3 && (
                            <th className="px-3 py-2 text-left font-medium text-gray-500">...</th>
                          )}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {tableData.data.slice(0, 8).map((row, rowIndex) => (
                          <tr key={rowIndex} className="hover:bg-gray-50">
                            {row.slice(0, 3).map((cell, cellIndex) => (
                              <td key={cellIndex} className="px-3 py-2 text-gray-900 truncate max-w-[80px]">
                                {String(cell).substring(0, 20)}
                                {String(cell).length > 20 && '...'}
                              </td>
                            ))}
                            {row.length > 3 && (
                              <td className="px-3 py-2 text-gray-500">...</td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {tableData.data.length > 8 && (
                    <div className="p-3 bg-gray-50 text-center">
                      <p className="text-xs text-gray-500">
                        +{tableData.data.length - 8} more rows
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
