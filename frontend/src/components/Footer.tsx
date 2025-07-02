
import { MessageCircle } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container mx-auto px-4 lg:px-8">
        <div className="max-w-6xl mx-auto">
          {/* Main Footer Content */}
          <div className="grid grid-cols-1 gap-8 mb-8">
            {/* Brand Column */}
            <div className="text-center">
              <div className="flex items-center justify-center space-x-2 mb-4">
                <MessageCircle className="h-6 w-6 text-blue-400" />
                <span className="text-2xl font-bold">chatfolio</span>
              </div>
              <p className="text-gray-400 mb-4 max-w-md mx-auto">
                Transform your investment experience with AI-powered portfolio conversations. 
                Get insights, track performance, and make smarter decisions.
              </p>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-400 text-sm">
              © 2024 chatfolio. All rights reserved.
            </div>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Privacy Policy</a>
              <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Terms of Service</a>
              <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Cookie Policy</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
