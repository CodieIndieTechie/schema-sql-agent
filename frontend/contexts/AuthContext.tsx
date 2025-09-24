"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import Cookies from 'js-cookie';

interface User {
  email: string;
  name: string;
  picture?: string;
  database_name?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => void;
  getToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated on app start
    const token = Cookies.get('auth_token');
    const userData = Cookies.get('user_data');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
      } catch (error) {
        console.error('Error parsing user data:', error);
        // Clear invalid data
        Cookies.remove('auth_token');
        Cookies.remove('user_data');
      }
    }
    
    setIsLoading(false);
  }, []);

  const login = (token: string, userData: User) => {
    console.log('🔐 AuthContext: Login called with:', { token: token ? 'present' : 'missing', userData });
    // Store token and user data in cookies
    Cookies.set('auth_token', token, { expires: 1 }); // 1 day expiry
    Cookies.set('user_data', JSON.stringify(userData), { expires: 1 });
    setUser(userData);
    console.log('✅ AuthContext: User state updated, isAuthenticated will be:', !!userData);
  };

  const logout = () => {
    // Remove token and user data
    Cookies.remove('auth_token');
    Cookies.remove('user_data');
    setUser(null);
  };

  const getToken = (): string | null => {
    return Cookies.get('auth_token') || null;
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    getToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
