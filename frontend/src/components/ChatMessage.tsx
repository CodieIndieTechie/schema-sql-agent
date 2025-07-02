
import { MessageCircle, User } from "lucide-react";

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  chartFile?: string;
  chartType?: string;
  hasChart?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`flex items-start space-x-3 max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-gradient-to-r from-blue-600 to-indigo-600' 
            : 'bg-white border border-blue-200/50 shadow-sm'
        }`}>
          {isUser ? (
            <User className="h-4 w-4 text-white" />
          ) : (
            <MessageCircle className="h-4 w-4 text-blue-600" />
          )}
        </div>

        {/* Message Content */}
        <div className={`rounded-2xl px-4 py-3 shadow-lg ${
          isUser 
            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-blue-500/20' 
            : 'bg-white border border-blue-100/50 shadow-blue-500/10'
        }`}>
          <p className={`text-sm leading-relaxed ${isUser ? 'text-white' : 'text-gray-700'}`}>
            {message.content}
          </p>
          
          {/* Chart Display */}
          {message.hasChart && message.chartFile && !isUser && (
            <div className="mt-4 border border-gray-200 rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-200">
                <p className="text-xs text-gray-600 font-medium">
                  📊 Interactive Chart ({message.chartType || 'auto'})
                </p>
              </div>
              <div className="bg-white">
                <iframe
                  src={`http://localhost:8001/charts/${message.chartFile}/embed`}
                  width="100%"
                  height="400"
                  frameBorder="0"
                  className="w-full"
                  title={`Chart: ${message.chartFile}`}
                />
              </div>
              <div className="bg-gray-50 px-3 py-2 border-t border-gray-200">
                <a 
                  href={`http://localhost:8001/charts/${message.chartFile}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  🔗 Open chart in new tab
                </a>
              </div>
            </div>
          )}
          
          <div className={`text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
