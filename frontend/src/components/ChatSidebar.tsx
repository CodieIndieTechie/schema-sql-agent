
"use client";

import { useState } from "react";
import { Menu, MessageSquare, Upload, Clock, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
}

interface ChatSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  uploadedFiles: UploadedFile[];
}

const ChatSidebar = ({ isOpen, onToggle, uploadedFiles }: ChatSidebarProps) => {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <>
      {/* Sidebar Toggle Button */}
      <Button
        onClick={onToggle}
        variant="ghost"
        size="sm"
        className="fixed top-4 left-4 z-50 hover:bg-gray-100"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full bg-white border-r border-gray-200 transition-transform duration-300 z-40 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } w-80`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Chat Menu</h2>
            <Button
              onClick={onToggle}
              variant="ghost"
              size="sm"
              className="hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-6">
              {/* Chat History Section */}
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <h3 className="text-sm font-medium text-gray-700">Recent Chats</h3>
                </div>
                <div className="space-y-2">
                  <div className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-gray-100">
                    <div className="text-sm text-gray-900 font-medium">Portfolio Analysis</div>
                    <div className="text-xs text-gray-500 mt-1">2 hours ago</div>
                  </div>
                  <div className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-gray-100">
                    <div className="text-sm text-gray-900 font-medium">Investment Strategy</div>
                    <div className="text-xs text-gray-500 mt-1">Yesterday</div>
                  </div>
                  <div className="p-3 rounded-lg hover:bg-gray-50 cursor-pointer border border-gray-100">
                    <div className="text-sm text-gray-900 font-medium">Mutual Fund Review</div>
                    <div className="text-xs text-gray-500 mt-1">3 days ago</div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Uploaded Files Section */}
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <Upload className="h-4 w-4 text-gray-500" />
                  <h3 className="text-sm font-medium text-gray-700">Uploaded Files</h3>
                  <span className="text-xs text-gray-400">({uploadedFiles.length}/10)</span>
                </div>
                
                {uploadedFiles.length === 0 ? (
                  <div className="text-xs text-gray-400 italic">No files uploaded yet</div>
                ) : (
                  <div className="space-y-2">
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="p-3 rounded-lg border border-gray-100 hover:bg-gray-50">
                        <div className="text-sm text-gray-900 font-medium truncate">{file.name}</div>
                        <div className="text-xs text-gray-500 mt-1">{formatFileSize(file.size)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-20 z-30"
          onClick={onToggle}
        />
      )}
    </>
  );
};

export default ChatSidebar;
