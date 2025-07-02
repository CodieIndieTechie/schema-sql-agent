
import { MessageCircle } from "lucide-react";
import ProfileSection from "./ProfileSection";

const ChatHeader = () => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-full mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <MessageCircle className="h-7 w-7 text-blue-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                chatfolio
              </h1>
            </div>
          </div>

          <ProfileSection />
        </div>
      </div>
    </header>
  );
};

export default ChatHeader;
