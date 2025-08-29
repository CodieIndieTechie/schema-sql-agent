"use client";

import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface GoogleAuthProps {
  buttonText?: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

const GoogleAuth: React.FC<GoogleAuthProps> = ({ 
  buttonText = "Continue with Google", 
  onSuccess,
  onError 
}) => {
  const { login } = useAuth();
  const router = useRouter();

  const handleSuccess = async (credentialResponse: any) => {
    try {
      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google');
      }

      // Send the Google ID token to our backend for verification
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await fetch(`${apiUrl}/auth/google/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id_token: credentialResponse.credential,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await response.json();
      
      // Login user with received token and user data
      login(data.access_token, data.user);
      
      // Call success callback if provided
      onSuccess?.();
      
      // Redirect to chat page
      router.push('/chat');
    } catch (error) {
      console.error('Google authentication error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      onError?.(errorMessage);
    }
  };

  const handleError = () => {
    console.error('Google authentication error');
    onError?.('Google authentication failed');
  };

  return (
    <div className="flex justify-center">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        useOneTap={false}
        text="continue_with"
        shape="rectangular"
        size="large"
        width="300"
      />
    </div>
  );
};

export default GoogleAuth;
