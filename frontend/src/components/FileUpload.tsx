"use client";

import { useState } from "react";
import { Paperclip, X, Upload, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { useRouter } from 'next/navigation';
import { useAuth } from "@/contexts/AuthContext";

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  status?: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  taskId?: string;
}

interface FileUploadProps {
  uploadedFiles: UploadedFile[];
  onFilesChange: (files: UploadedFile[]) => void;
}

const FileUpload = ({ uploadedFiles, onFilesChange }: FileUploadProps) => {
  const { getToken, logout } = useAuth();
  const router = useRouter();
  const [isUploading, setIsUploading] = useState(false);
  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv'
    ];
    
    const allowedExtensions = ['.xls', '.xlsx', '.csv'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      toast({
        title: "Invalid file type",
        description: "Please upload only Excel (.xls, .xlsx) or CSV files.",
        variant: "destructive"
      });
      return false;
    }

    return true;
  };

  const uploadFilesToBackend = async (filesToUpload: File[]) => {
    setIsUploading(true);
    const formData = new FormData();
    
    filesToUpload.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const token = getToken();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      
      // Debug token
      console.log('Token for upload:', token ? 'Token present' : 'No token found');
      
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }
      
      const response = await fetch(`${apiUrl}/upload-files`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload response error:', response.status, response.statusText, errorText);
        
        if (response.status === 401) {
          // Token expired or invalid - force re-login
          toast({
            title: "Session Expired",
            description: "Your session has expired. Please log in again.",
            variant: "destructive",
          });
          logout();
          router.push('/');
          throw new Error('Session expired. Redirecting to login...');
        }
        
        throw new Error(`Upload failed: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      
      toast({
        title: "Files uploaded successfully!",
        description: `${filesToUpload.length} file(s) are being processed and will appear in your database shortly.`,
      });

      return result;
    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload files to server.",
        variant: "destructive"
      });
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    const newFiles: UploadedFile[] = [];
    const filesToUpload: File[] = [];
    let totalSize = uploadedFiles.reduce((sum, file) => sum + file.size, 0);

    if (uploadedFiles.length + files.length > 10) {
      toast({
        title: "File limit exceeded",
        description: "You can upload a maximum of 10 files.",
        variant: "destructive"
      });
      return;
    }

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      if (!validateFile(file)) continue;

      if (totalSize + file.size > 100 * 1024 * 1024) {
        toast({
          title: "Size limit exceeded",
          description: "Total file size cannot exceed 100MB.",
          variant: "destructive"
        });
        break;
      }

      totalSize += file.size;
      filesToUpload.push(file);
      newFiles.push({
        id: Date.now().toString() + i,
        name: file.name,
        size: file.size,
        status: 'pending'
      });
    }

    if (newFiles.length > 0) {
      // Add files to UI first with pending status
      onFilesChange([...uploadedFiles, ...newFiles]);
      
      // Update status to uploading
      const updatedFiles = [...uploadedFiles, ...newFiles.map(f => ({ ...f, status: 'uploading' as const }))];
      onFilesChange(updatedFiles);
      
      try {
        // Upload files to backend
        const result = await uploadFilesToBackend(filesToUpload);
        
        // Update status to processing
        const processingFiles = updatedFiles.map(f => 
          newFiles.find(nf => nf.id === f.id) 
            ? { ...f, status: 'processing' as const, taskId: result.task_id }
            : f
        );
        onFilesChange(processingFiles);
        
        // Auto-update to completed after a delay (you might want to implement task status polling)
        setTimeout(() => {
          const completedFiles = processingFiles.map(f => 
            newFiles.find(nf => nf.id === f.id) 
              ? { ...f, status: 'completed' as const }
              : f
          );
          onFilesChange(completedFiles);
        }, 5000);
        
      } catch (error) {
        // Update status to error
        const errorFiles = updatedFiles.map(f => 
          newFiles.find(nf => nf.id === f.id) 
            ? { ...f, status: 'error' as const }
            : f
        );
        onFilesChange(errorFiles);
      }
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFileUpload(e.target.files);
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'uploading': return <Upload className="h-3 w-3 text-blue-600 animate-spin" />;
      case 'processing': return <Upload className="h-3 w-3 text-yellow-600 animate-pulse" />;
      case 'completed': return <CheckCircle className="h-3 w-3 text-green-600" />;
      case 'error': return <X className="h-3 w-3 text-red-600" />;
      default: return null;
    }
  };

  const removeFile = (fileId: string) => {
    onFilesChange(uploadedFiles.filter(f => f.id !== fileId));
  };

  return (
    <div>
      <input
        type="file"
        id="file-upload"
        multiple
        accept=".xls,.xlsx,.csv"
        onChange={handleFileInputChange}
        className="hidden"
      />
      <label htmlFor="file-upload">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="p-2 hover:bg-gray-100 rounded-full"
          disabled={isUploading}
          asChild
        >
          <span className="cursor-pointer">
            {isUploading ? (
              <Upload className="h-5 w-5 text-blue-600 animate-spin" />
            ) : (
              <Paperclip className="h-5 w-5 text-gray-600" />
            )}
          </span>
        </Button>
      </label>
    </div>
  );
};

export default FileUpload;
