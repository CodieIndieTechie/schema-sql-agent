'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { GoogleAuth } from '../components/auth/GoogleAuth'
import { 
  Send, 
  Upload, 
  Database, 
  User, 
  MessageSquare, 
  FileSpreadsheet,
  Loader2,
  ChevronDown,
  ChevronUp,
  Table,
  Bot,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2
} from 'lucide-react'

// Types
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

interface UploadResult {
  success: boolean
  message: string
  tables_created: string[]
  total_rows: number
  sheets_processed: number
  files_processed: number
  errors: string[]
}

interface AsyncUploadResponse {
  task_id: string
  status: string
  message: string
  user_id: string
}

interface FileResult {
  file: string
  success: boolean
  result: UploadResult
}

interface TaskStatusResponse {
  task_id: string
  state: string
  status: string
  current: number
  total: number
  files_processed: number
  sheets_processed: number
  result?: FileResult[]
  error?: string[]
}

interface AuthUser {
  email: string
  name: string
  picture?: string
  database_name: string
}

interface TableInfo {
  table_name: string
  source_file: string
  sheet_name?: string
  uploaded_at: string
}

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8001'

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('jwt_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Helper function to check if user is authenticated
const isAuthenticated = () => {
  return !!localStorage.getItem('jwt_token')
}

export default function MultiTenantSQLAgent() {
  // State management
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [tables, setTables] = useState<TableInfo[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadAreaOpen, setUploadAreaOpen] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number } | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Authentication check
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      if (!isAuthenticated()) {
        setAuthLoading(false)
        return
      }

      const response = await axios.get(`${API_BASE_URL}/auth/me`, { headers: getAuthHeaders() })
      setCurrentUser(response.data)
      setAuthLoading(false)
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('jwt_token')
      setAuthLoading(false)
    }
  }

  // Initialize user data only if authenticated
  useEffect(() => {
    if (currentUser && !authLoading) {
      loadUserData()
    }
  }, [currentUser, authLoading])

  const loadUserData = async () => {
    try {
      // Load tables for authenticated user
      const tablesResponse = await axios.get(`${API_BASE_URL}/user/tables`, { headers: getAuthHeaders() })
      setTables(tablesResponse.data.tables || [])
    } catch (error) {
      console.error('Failed to load user data:', error)
    }
  }

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendQuery = async () => {
    if (!inputValue.trim() || !currentUser) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setInputValue('')

    try {
      const response = await axios.post(`${API_BASE_URL}/query`, {
        query: inputValue.trim()
      }, { headers: getAuthHeaders() })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Query failed:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to process query'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendQuery()
    }
  }

  const onDrop = (acceptedFiles: File[]) => {
    setUploadedFiles(prev => [...prev, ...acceptedFiles])
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    multiple: true
  })

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const uploadFiles = async (files: File[]) => {
    if (!currentUser) {
      alert('Please sign in to upload files')
      return
    }

    setIsUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      files.forEach(file => formData.append('files', file))

      const response = await axios.post(`${API_BASE_URL}/upload-files`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getAuthHeaders()
        },
      })

      if (response.data.task_id) {
        setCurrentTaskId(response.data.task_id)
        setIsPolling(true)
        setUploadProgress({ current: 0, total: files.length })
        
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: `🔄 Processing ${files.length} file(s) in the background. Task ID: ${response.data.task_id}`,
          timestamp: new Date().toISOString()
        }])

        pollTaskStatus(response.data.task_id)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      alert(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    const maxAttempts = 60 // 5 minutes max (5 second intervals)
    let attempts = 0

    const poll = async () => {
      try {
        attempts++
        const response = await axios.get(`${API_BASE_URL}/task-status/${taskId}`, { headers: getAuthHeaders() })
        const status: TaskStatusResponse = response.data

        // Update progress message
        const progressMessage: Message = {
          id: `progress-${taskId}`,
          role: 'system',
          content: `📊 Processing progress: ${status.current}/${status.total} steps completed\n` +
                  `Files processed: ${status.files_processed}\n` +
                  `Sheets processed: ${status.sheets_processed}\n` +
                  `Status: ${status.status}`,
          timestamp: new Date().toISOString()
        }

        // Update or add progress message
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.id !== `progress-${taskId}`)
          return [...filtered, progressMessage]
        })

        if (status.state === 'SUCCESS' && status.result) {
          // Task completed successfully
          const allSuccessful = status.result.every(fileResult => fileResult.success);
          
          let message = '';
          let tablesCreated: string[] = [];
          let totalRows = 0;
          
          if (allSuccessful) {
            tablesCreated = status.result.reduce((tables, fileResult) => 
              tables.concat(fileResult.result.tables_created || []), [] as string[]);
            totalRows = status.result.reduce((sum, fileResult) => sum + (fileResult.result.total_rows || 0), 0);
            message = `Successfully uploaded ${status.files_processed} file(s) with ${status.sheets_processed} sheet(s)`;
          } else {
            message = `Partially successful: ${status.files_processed} file(s) uploaded, ${status.files_processed - status.result.filter(fileResult => fileResult.success).length} failed`;
          }
          
          const finalMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: allSuccessful ? 
              `✅ ${message}\n\nTables created: ${tablesCreated.join(', ')}\nTotal rows: ${totalRows}` :
              `❌ Upload failed: ${message}`,
            timestamp: new Date().toISOString()
          }
          
          setMessages(prev => {
            const filtered = prev.filter(msg => msg.id !== `progress-${taskId}`)
            return [...filtered, finalMessage]
          })

          loadUserData()
          return
        } else if (status.state === 'FAILURE') {
          // Task failed
          let errorDetail = status.error || status.status || 'Unknown error';
          if (Array.isArray(errorDetail)) errorDetail = errorDetail.join('\n');
          const errorMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: `❌ File processing failed: ${errorDetail}`,
            timestamp: new Date().toISOString()
          }
          setMessages(prev => {
            const filtered = prev.filter(msg => msg.id !== `progress-${taskId}`)
            return [...filtered, errorMessage]
          })
          return
        } else if (attempts >= maxAttempts) {
          // Timeout
          const timeoutMessage: Message = {
            id: Date.now().toString(),
            role: 'system',
            content: '⏰ File processing is taking longer than expected. Please check back later or try uploading again.',
            timestamp: new Date().toISOString()
          }
          
          setMessages(prev => {
            const filtered = prev.filter(msg => msg.id !== `progress-${taskId}`)
            return [...filtered, timeoutMessage]
          })
          return
        }

        // Continue polling
        setTimeout(poll, 5000) // Poll every 5 seconds
      } catch (error) {
        console.error('Error polling task status:', error)
        const errorMessage: Message = {
          id: Date.now().toString(),
          role: 'system',
          content: '❌ Error checking upload progress. Please try again.',
          timestamp: new Date().toISOString()
        }
        
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.id !== `progress-${taskId}`)
          return [...filtered, errorMessage]
        })
      }
    }

    // Start polling after a short delay
    setTimeout(poll, 2000)
  }

  const createNewSession = async () => {
    // Removed session management code
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const getMessageIcon = (role: string) => {
    switch (role) {
      case 'user':
        return <User className="w-6 h-6 text-white" />
      case 'assistant':
        return <Bot className="w-6 h-6 text-white" />
      case 'system':
        return <AlertCircle className="w-6 h-6 text-white" />
      default:
        return <MessageSquare className="w-6 h-6 text-white" />
    }
  }

  const getMessageBgColor = (role: string) => {
    switch (role) {
      case 'user':
        return 'bg-gray-900'
      case 'assistant':
        return 'bg-gray-600'
      case 'system':
        return 'bg-yellow-600'
      default:
        return 'bg-gray-500'
    }
  }

  // Show loading screen during auth check
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Show authentication component if not authenticated
  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">
                Multi-Tenant SQL Agent
              </h1>
              <p className="text-xl text-gray-600">
                Natural language interface for your databases with secure authentication
              </p>
            </div>
            <GoogleAuth />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center">
                <Database className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-xl font-semibold text-gray-900">Multi-Tenant SQL Agent</h1>
            </div>
            
            {currentUser && (
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center space-x-1">
                  <User className="w-4 h-4" />
                  <span>Authenticated as {currentUser.name}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Database className="w-4 h-4" />
                  <span>DB: {currentUser.database_name}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <Table className="w-4 h-4" />
                  <span>{tables.length} tables</span>
                </span>
              </div>
            )}
          </div>

          <GoogleAuth />
          <button
            onClick={createNewSession}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm"
          >
            New Session
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Sidebar */}
        <div className="w-80 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto">
          <div className="space-y-6">
            {/* Upload Section */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <button
                onClick={() => setUploadAreaOpen(!uploadAreaOpen)}
                className="w-full flex items-center justify-between text-left"
              >
                <div className="flex items-center space-x-2">
                  <Upload className="w-5 h-5 text-gray-600" />
                  <span className="font-medium text-gray-900">Upload Files</span>
                </div>
                {uploadAreaOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {uploadAreaOpen && (
                <div className="mt-4 space-y-4">
                  <div
                    {...getRootProps()}
                    className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                      isDragActive ? 'border-gray-400 bg-gray-50' : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <input {...getInputProps()} />
                    <FileSpreadsheet className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">
                      {isDragActive ? 'Drop files here...' : 'Drag & drop Excel/CSV files'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">or click to browse</p>
                  </div>

                  {uploadedFiles.length > 0 && (
                    <div className="space-y-2">
                      {uploadedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 rounded p-2">
                          <span className="text-sm text-gray-700 truncate">{file.name}</span>
                          <button
                            onClick={() => removeFile(index)}
                            className="text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                      
                      <button
                        onClick={() => uploadFiles(uploadedFiles)}
                        disabled={isUploading}
                        className="w-full bg-gray-900 text-white py-2 px-4 rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                      >
                        {isUploading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Uploading...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="w-4 h-4" />
                            <span>Upload {uploadedFiles.length} file(s)</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Tables Section */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center space-x-2 mb-4">
                <Table className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">Your Tables ({tables.length})</span>
              </div>

              {tables.length === 0 ? (
                <p className="text-sm text-gray-500">No tables uploaded yet</p>
              ) : (
                <div className="space-y-2">
                  {tables.map((table, index) => (
                    <div key={index} className="bg-gray-50 rounded p-3">
                      <div className="font-medium text-sm text-gray-900">{table.table_name}</div>
                      <div className="text-xs text-gray-600 mt-1">
                        <div>From: {table.source_file}</div>
                        {table.sheet_name && <div>Sheet: {table.sheet_name}</div>}
                        <div className="flex items-center space-x-1 mt-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(table.uploaded_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div key={message.id} className="flex space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${getMessageBgColor(message.role)}`}>
                  {getMessageIcon(message.role)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-medium text-gray-900 capitalize">{message.role}</span>
                    <span className="text-xs text-gray-500">{formatTimestamp(message.timestamp)}</span>
                  </div>
                  <div className="text-gray-700 whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex space-x-3">
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-medium text-gray-900">Assistant</span>
                    <span className="text-xs text-gray-500">thinking...</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing your query...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-6">
            <div className="flex space-x-4">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about your data..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-gray-500 focus:border-transparent"
                  rows={3}
                  disabled={isLoading || !currentUser}
                />
              </div>
              <button
                onClick={sendQuery}
                disabled={!inputValue.trim() || isLoading || !currentUser}
                className="bg-gray-900 text-white p-3 rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
