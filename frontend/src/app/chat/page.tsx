import ChatInterface from "@/components/ChatInterface";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function Chat() {
  return (
    <ProtectedRoute>
      <div className="h-screen bg-gray-50">
        <ChatInterface />
      </div>
    </ProtectedRoute>
  );
}
