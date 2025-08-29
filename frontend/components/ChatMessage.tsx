
import { MessageCircle, User } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

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
          {isUser ? (
            <p className={`text-sm leading-relaxed ${isUser ? 'text-white' : 'text-gray-700'}`}>
              {message.content}
            </p>
          ) : (
            <div className={`text-sm leading-relaxed ${isUser ? 'text-white' : 'text-gray-700'} prose prose-sm max-w-none`}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw, rehypeSanitize]}
                components={{
                  // Custom styling for markdown elements
                  h1: ({node, ...props}) => <h1 className="text-lg font-bold mb-2 text-gray-800" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-base font-bold mb-2 text-gray-800" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-sm font-bold mb-1 text-gray-800" {...props} />,
                  p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-bold text-gray-900" {...props} />,
                  em: ({node, ...props}) => <em className="italic" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc ml-4 mb-2" {...props} />,
                  ol: ({node, ...props}) => <ol className="list-decimal ml-4 mb-2" {...props} />,
                  li: ({node, ...props}) => <li className="mb-1" {...props} />,
                  code: ({node, inline, ...props}) => 
                    inline ? (
                      <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono text-gray-800" {...props} />
                    ) : (
                      <code className="block bg-gray-100 p-2 rounded text-xs font-mono text-gray-800 overflow-x-auto" {...props} />
                    ),
                  pre: ({node, ...props}) => <pre className="bg-gray-100 p-2 rounded mb-2 overflow-x-auto" {...props} />,
                  table: ({node, ...props}) => (
                    <div className="overflow-x-auto mb-2">
                      <table className="min-w-full border-collapse border border-gray-300 text-xs" {...props} />
                    </div>
                  ),
                  th: ({node, ...props}) => <th className="border border-gray-300 px-2 py-1 bg-gray-50 font-bold text-left" {...props} />,
                  td: ({node, ...props}) => <td className="border border-gray-300 px-2 py-1" {...props} />,
                  hr: ({node, ...props}) => <hr className="my-3 border-gray-300" {...props} />,
                  blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-blue-500 pl-3 italic text-gray-600 mb-2" {...props} />
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
          
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
