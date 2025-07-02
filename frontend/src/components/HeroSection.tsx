"use client";

import { MessageCircle, TrendingUp, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import Link from 'next/link';
import GoogleAuth from '@/components/GoogleAuth';
import { useAuth } from '@/contexts/AuthContext';

const HeroSection = () => {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/chat');
  };

  return (
    <section className="relative bg-gradient-to-br from-slate-50 via-white to-blue-50/30 py-20 lg:py-32 overflow-hidden">
      <div className="container mx-auto px-4 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Logo/Brand with animated entrance */}
          <div className="flex items-center justify-center mb-12 animate-fade-in">
            <div className="flex items-center space-x-3 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-lg shadow-blue-500/10 border border-blue-100/50">
              <div className="relative">
                <MessageCircle className="h-8 w-8 text-blue-600" />
                <div className="absolute -inset-1 bg-blue-600/20 rounded-full blur-sm opacity-60 animate-pulse"></div>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                chatfolio
              </span>
            </div>
          </div>

          {/* Hero Headline with sophisticated typography */}
          <div className="mb-8 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 mb-4 leading-tight">
              Chat with Your
            </h1>
            <div className="relative inline-block">
              <h1 className="text-4xl lg:text-6xl font-bold bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 bg-clip-text text-transparent leading-tight">
                Mutual Fund Portfolio
              </h1>
              <div className="absolute -inset-4 bg-gradient-to-r from-blue-200/40 to-indigo-200/40 blur-2xl rounded-2xl opacity-30 -z-10"></div>
            </div>
          </div>

          {/* Subheadline with refined spacing */}
          <p className="text-xl lg:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed animate-fade-in" style={{ animationDelay: '0.4s' }}>
            Get instant insights, track performance, and make informed investment decisions through natural conversation with your portfolio data.
          </p>

          {/* Prominent CTA Button */}
          <div className="flex justify-center mb-6 animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <div className="flex justify-center items-center">
              {isAuthenticated ? (
                <Link href="/chat">
                  <Button size="lg" className="px-8 py-4 text-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105">
                    <MessageCircle className="mr-2 h-5 w-5" />
                    Go to Chat
                  </Button>
                </Link>
              ) : (
                <div className="transform transition-all duration-300 hover:scale-105">
                  <div className="relative p-1 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-xl shadow-lg hover:shadow-xl">
                    <div className="bg-white rounded-lg p-1">
                      <GoogleAuth
                        buttonText="Continue with Google"
                        onSuccess={() => console.log('Authentication successful!')}
                        onError={(error) => console.error('Authentication error:', error)}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Refined Privacy Text */}
          <div className="mb-16 animate-fade-in" style={{ animationDelay: '0.8s' }}>
            <p className="text-sm text-gray-500 max-w-md mx-auto bg-white/60 backdrop-blur-sm px-4 py-2 rounded-lg border border-gray-100/50">
              Your financial data is encrypted and secure with highly secure protection.
            </p>
          </div>

          {/* Enhanced Trust Indicators */}
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-6 sm:space-y-0 sm:space-x-12 animate-fade-in" style={{ animationDelay: '1s' }}>
            {[
              { icon: Shield, text: "Highly Secure", delay: "0ms" },
              { icon: TrendingUp, text: "Real-Time Data", delay: "100ms" },
              { icon: MessageCircle, text: "AI-Powered Insights", delay: "200ms" }
            ].map((item, index) => {
              const IconComponent = item.icon;
              return (
                <div 
                  key={index} 
                  className="group flex items-center space-x-3 bg-white/70 backdrop-blur-sm px-6 py-3 rounded-xl shadow-md shadow-gray-500/5 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300 hover:scale-105 border border-gray-100/50"
                  style={{ animationDelay: item.delay }}
                >
                  <div className="relative">
                    <IconComponent className="h-5 w-5 text-gray-600 group-hover:text-blue-600 transition-colors duration-300" />
                    <div className="absolute -inset-1 bg-blue-500/20 rounded-full blur-sm opacity-0 group-hover:opacity-60 transition-opacity duration-300"></div>
                  </div>
                  <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 transition-colors duration-300">
                    {item.text}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Sophisticated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Main ambient glow */}
        <div className="absolute top-1/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-blue-200/30 to-indigo-200/30 rounded-full blur-3xl opacity-60 animate-pulse"></div>
        
        {/* Floating elements */}
        <div className="absolute top-1/4 right-1/4 transform w-32 h-32 bg-gradient-to-br from-blue-300/20 to-transparent rounded-full blur-2xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-1/3 left-1/4 transform w-24 h-24 bg-gradient-to-tl from-indigo-300/20 to-transparent rounded-full blur-xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3e%3cdefs%3e%3cpattern id='grid' width='60' height='60' patternUnits='userSpaceOnUse'%3e%3cpath d='m 36 14 h 4 v 4 h -4 z m -30 0 h 4 v 4 h -4 z m 15 15 h 4 v 4 h -4 z m -15 15 h 4 v 4 h -4 z m 30 0 h 4 v 4 h -4 z' fill='%23f1f5f9' fill-opacity='0.3'/%3e%3c/pattern%3e%3c/defs%3e%3crect width='100%25' height='100%25' fill='url(%23grid)'/%3e%3c/svg%3e")`,
          }}></div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
