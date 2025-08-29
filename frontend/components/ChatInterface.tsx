"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { useRouter } from "next/navigation";
import ChatMessage from "./ChatMessage";
import ChatHeader from "./ChatHeader";
import FileUpload from "./FileUpload";
import CollapsibleNavbar from "./CollapsibleNavbar";
import { useAuth } from "../contexts/AuthContext";

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  chartFile?: string;
  chartType?: string;
  hasChart?: boolean;
}

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status?: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  taskId?: string;
}

const ChatInterface = () => {
  const { getToken } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your SQL Agent assistant. I can help you query your database, upload CSV/Excel files, and create charts from your data. What would you like to know?",
      role: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Get the JWT token using AuthContext method
      const token = getToken();
      
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Call our backend API with authentication
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: inputMessage,
          session_id: 'chat-session-' + Date.now() // Generate unique session ID
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Check if response contains chart data
      let chartFile = undefined;
      let chartType = undefined;
      let hasChart = false;
      
      // Parse the response for chart information
      if (data.response && typeof data.response === 'string') {
        // Look for chart references in the response text
        const chartMatch = data.response.match(/chart_[a-zA-Z0-9_]+\.html/);
        if (chartMatch) {
          chartFile = chartMatch[0];
          hasChart = true;
          chartType = 'auto'; // Default type
        }
      }
      
      // Also check if there's explicit chart data in the response
      if (data.chart_file) {
        chartFile = data.chart_file;
        chartType = data.chart_type || 'auto';
        hasChart = true;
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response || data.message || 'Sorry, I could not process your request.',
        role: 'assistant',
        timestamp: new Date(),
        chartFile,
        chartType,
        hasChart
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error calling API:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <ChatHeader />
      
      <div className="flex flex-1 overflow-hidden">
        <CollapsibleNavbar uploadedFiles={uploadedFiles} />
        
        <div className="flex-1 flex flex-col min-w-0">
          {/* Messages Area */}
          <div className="flex-1 overflow-hidden relative">
            <div className="h-full max-w-4xl mx-auto w-full px-4 py-6 pr-8">
              <ScrollArea className="h-full [&>[data-radix-scroll-area-scrollbar]]:!right-2 [&>[data-radix-scroll-area-scrollbar]]:!fixed [&>[data-radix-scroll-area-scrollbar]]:!z-50">
                <div className="space-y-6 pb-6 pr-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white rounded-2xl px-4 py-3 max-w-xs shadow-sm border border-gray-100">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                        <span className="text-sm text-gray-500">AI is thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                </div>
              </ScrollArea>
            </div>
          </div>

          {/* Input Area - Gemini Style */}
          <div className="bg-gray-50 p-4 border-t">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-3xl border border-gray-200 shadow-lg p-4">
                <div className="flex items-center space-x-3">
                  {/* Text Input */}
                  <div className="flex-1">
                    <Textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Message Chatfolio - Ask about your portfolio, investments, or market analysis"
                      className="border-0 resize-none focus:ring-0 focus:outline-none shadow-none bg-transparent text-base p-0 min-h-[24px] max-h-32 placeholder:text-gray-500 placeholder:italic flex items-center"
                      disabled={isLoading}
                    />
                  </div>

                  {/* Right Side Buttons */}
                  <div className="flex items-center space-x-2">
                    <FileUpload
                      uploadedFiles={uploadedFiles}
                      onFilesChange={setUploadedFiles}
                    />

                    <Button
                      onClick={handleSendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      size="sm"
                      className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-2 disabled:opacity-50"
                    >
                      <Send className="h-5 w-5" />
                    </Button>
                  </div>
                </div>

                {/* File Upload Area */}
                {uploadedFiles.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="text-xs text-gray-500 mb-2">
                      Uploaded files ({uploadedFiles.length}/10):
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {uploadedFiles.map((file) => {
                        const getStatusColor = (status?: string) => {
                          switch (status) {
                            case 'uploading': return 'bg-blue-50 border-blue-200 text-blue-700';
                            case 'processing': return 'bg-yellow-50 border-yellow-200 text-yellow-700';
                            case 'completed': return 'bg-green-50 border-green-200 text-green-700';
                            case 'error': return 'bg-red-50 border-red-200 text-red-700';
                            default: return 'bg-gray-50 border-gray-200 text-gray-700';
                          }
                        };
                        
                        const getStatusText = (status?: string) => {
                          switch (status) {
                            case 'uploading': return ' (uploading...)';
                            case 'processing': return ' (processing...)';
                            case 'completed': return ' ✓';
                            case 'error': return ' ✗';
                            default: return '';
                          }
                        };
                        
                        return (
                          <div key={file.id} className={`${getStatusColor(file.status)} border rounded-lg px-3 py-1 text-xs flex items-center gap-1`}>
                            <span>{file.name}{getStatusText(file.status)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
