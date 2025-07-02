"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageSquare, Upload, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
}

interface CollapsibleNavbarProps {
  uploadedFiles: UploadedFile[];
}

const CollapsibleNavbar = ({ uploadedFiles }: CollapsibleNavbarProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const mockChatHistory = [
    { id: '1', title: 'SQL Query Analysis', timestamp: '2 hours ago' },
    { id: '2', title: 'Data Upload Session', timestamp: 'Yesterday' },
    { id: '3', title: 'Chart Generation', timestamp: '3 days ago' },
  ];

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
                {mockChatHistory.map((chat) => (
                  <div
                    key={chat.id}
                    className="p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start space-x-2">
                      <MessageSquare className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-700 truncate">
                          {chat.title}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {chat.timestamp}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
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
