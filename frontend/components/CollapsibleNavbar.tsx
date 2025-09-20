"use client";

import { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight, MessageSquare, Upload, Clock, Plus, MoreHorizontal, Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "./ui/dropdown-menu";
import { useAuth } from "../contexts/AuthContext";
import { getUserSessions, getSessionMessages, createNewSession, deleteSession, generateChatTitle, formatRelativeTime, ChatSession, ChatMessage } from "../lib/api";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
}

interface CollapsibleNavbarProps {
  uploadedFiles: UploadedFile[];
  currentSessionId?: string;
  onSessionChange?: (sessionId: string) => void;
  onNewChat?: () => void;
}

const CollapsibleNavbar = ({ uploadedFiles, currentSessionId, onSessionChange, onNewChat }: CollapsibleNavbarProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [sessionTitles, setSessionTitles] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const { user, getToken } = useAuth();

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Load chat sessions and generate titles
  useEffect(() => {
    const loadChatSessions = async () => {
      if (!user?.email) return;
      
      const token = getToken();
      if (!token) return;

      setIsLoading(true);
      try {
        const sessions = await getUserSessions(user.email, token);
        setChatSessions(sessions);

        // Generate titles for sessions by getting their first message
        const titles: Record<string, string> = {};
        for (const session of sessions) {
          if (session.session_name) {
            titles[session.session_id] = session.session_name;
          } else {
            // Get first user message to generate title
            const messages = await getSessionMessages(session.session_id, token);
            const firstUserMessage = messages.find(msg => msg.message_type === 'human');
            titles[session.session_id] = firstUserMessage 
              ? generateChatTitle(firstUserMessage.content)
              : 'New Chat';
          }
        }
        setSessionTitles(titles);
      } catch (error) {
        console.error('Error loading chat sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadChatSessions();
  }, [user?.email, getToken]);

  const handleNewChat = async () => {
    if (!user?.email) return;
    
    const token = getToken();
    if (!token) return;

    try {
      const newSession = await createNewSession(user.email, null, token);
      if (newSession) {
        setChatSessions(prev => [newSession, ...prev]);
        setSessionTitles(prev => ({ ...prev, [newSession.session_id]: 'New Chat' }));
        onNewChat?.();
        onSessionChange?.(newSession.session_id);
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  const handleDeleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this chat?')) return;
    
    const token = getToken();
    if (!token) return;

    try {
      const success = await deleteSession(sessionId, token);
      if (success) {
        setChatSessions(prev => prev.filter(s => s.session_id !== sessionId));
        setSessionTitles(prev => {
          const newTitles = { ...prev };
          delete newTitles[sessionId];
          return newTitles;
        });
        
        // If deleted session was current, switch to first available or create new
        if (currentSessionId === sessionId) {
          const remainingSessions = chatSessions.filter(s => s.session_id !== sessionId);
          if (remainingSessions.length > 0) {
            onSessionChange?.(remainingSessions[0].session_id);
          } else {
            handleNewChat();
          }
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    onSessionChange?.(sessionId);
  };

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-80'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col h-full`}>
      <ScrollArea className="flex-1 h-full">
        <div className={`${isCollapsed ? 'p-2' : 'p-4'} space-y-6 h-full`}>
          {/* Toggle button integrated with Chat History Section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-gray-500" />
                {!isCollapsed && (
                  <h3 className="text-sm font-medium text-gray-700">Recent Chats</h3>
                )}
              </div>
              <Button
                onClick={() => setIsCollapsed(!isCollapsed)}
                variant="ghost"
                size="sm"
                className="hover:bg-gray-100 p-1"
              >
                {isCollapsed ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            </div>
            
            {!isCollapsed && (
              <div className="space-y-2">
                {/* New Chat Button */}
                <Button
                  onClick={handleNewChat}
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-left h-auto p-3 border-dashed border-gray-300 hover:border-gray-400 hover:bg-gray-50"
                >
                  <Plus className="h-4 w-4 mr-2 text-gray-500" />
                  <span className="text-sm text-gray-600">New Chat</span>
                </Button>

                {/* Chat Sessions */}
                {isLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="p-3 rounded-lg border border-gray-100 animate-pulse">
                        <div className="h-4 bg-gray-200 rounded mb-2"></div>
                        <div className="h-3 bg-gray-100 rounded w-2/3"></div>
                      </div>
                    ))}
                  </div>
                ) : chatSessions.length > 0 ? (
                  chatSessions.map((session) => (
                    <div
                      key={session.session_id}
                      onClick={() => handleSessionClick(session.session_id)}
                      className={`p-3 rounded-lg border transition-colors cursor-pointer group ${
                        currentSessionId === session.session_id
                          ? 'border-blue-200 bg-blue-50'
                          : 'border-gray-100 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start space-x-2">
                        <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm font-medium truncate ${
                            currentSessionId === session.session_id
                              ? 'text-blue-700'
                              : 'text-gray-700'
                          }`}>
                            {sessionTitles[session.session_id] || 'New Chat'}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatRelativeTime(session.updated_at)}
                          </p>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 h-auto"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreHorizontal className="h-4 w-4 text-gray-400" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => handleDeleteSession(session.session_id, e)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete Chat
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6">
                    <MessageSquare className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No chats yet</p>
                    <p className="text-xs text-gray-400 mt-1">Start a new conversation</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <Separator />

          {/* Uploaded Files Section */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Upload className="h-4 w-4 text-gray-500" />
              {!isCollapsed && (
                <h3 className="text-sm font-medium text-gray-700">Uploaded Files</h3>
              )}
            </div>
            
            {!isCollapsed && (
              <div className="space-y-2">
                {uploadedFiles.length > 0 ? (
                  uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Upload className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-700 truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(file.size)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6">
                    <Upload className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">No files uploaded yet</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
};

export default CollapsibleNavbar;
