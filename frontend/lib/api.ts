// API functions for chat session management

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface ChatSession {
  session_id: string;
  user_email: string;
  session_name: string | null;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count?: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  message_type: 'human' | 'ai' | 'system';
  content: string;
  timestamp: string;
  message_metadata?: string;
  chart_files?: string;
  query_results?: string;
}

// Get user's chat sessions
export async function getUserSessions(userEmail: string, token: string): Promise<ChatSession[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions/user/${encodeURIComponent(userEmail)}?limit=50`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch sessions: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user sessions:', error);
    return [];
  }
}

// Get session messages
export async function getSessionMessages(sessionId: string, token: string): Promise<ChatMessage[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions/messages/${sessionId}?limit=100`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch messages: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching session messages:', error);
    return [];
  }
}

// Create new chat session
export async function createNewSession(userEmail: string, sessionName: string | null, token: string): Promise<ChatSession | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions/create`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_email: userEmail,
        session_name: sessionName,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating new session:', error);
    return null;
  }
}

// Delete chat session (assuming we have this endpoint)
export async function deleteSession(sessionId: string, token: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch (error) {
    console.error('Error deleting session:', error);
    return false;
  }
}

// Generate chat title from first user message
export function generateChatTitle(firstMessage: string): string {
  if (!firstMessage || firstMessage.trim().length === 0) {
    return 'New Chat';
  }

  // Clean and truncate the message
  const cleaned = firstMessage.trim().replace(/\s+/g, ' ');
  
  // If message is short enough, use it as is
  if (cleaned.length <= 50) {
    return cleaned;
  }

  // Truncate at word boundary
  const truncated = cleaned.substring(0, 47);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > 20) {
    return truncated.substring(0, lastSpace) + '...';
  }
  
  return truncated + '...';
}

// Format relative time
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 1) {
    return 'Just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  } else if (diffInDays === 1) {
    return 'Yesterday';
  } else if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}
