# Comprehensive Memory & Session Management System

## Overview

The SQL Agent system now includes a robust memory and session management system that provides:

- **Persistent Chat History** - Conversations survive browser refresh and system restarts
- **Cross-Session Memory** - Agents remember previous conversations and user preferences
- **Context Awareness** - Enhanced responses using conversation history
- **Multi-User Support** - Isolated sessions per user with proper authentication
- **Frontend Persistence** - localStorage integration for seamless user experience

## Architecture Components

### 1. Database Schema

#### Chat Sessions (`chat_sessions`)
```sql
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255) NOT NULL,
    session_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    session_metadata TEXT
);
```

#### Chat History (`chat_history`)
```sql
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id),
    message_type VARCHAR(50) NOT NULL, -- 'human', 'ai', 'system'
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_metadata TEXT, -- JSON string for additional metadata
    chart_files TEXT,      -- JSON array of chart filenames
    query_results TEXT     -- JSON string for SQL query results
);
```

#### Conversation Context (`conversation_contexts`)
```sql
CREATE TABLE conversation_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id),
    context_type VARCHAR(50) NOT NULL, -- 'data_context', 'chart_context', 'query_context', 'user_preference'
    context_key VARCHAR(255) NOT NULL,
    context_value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(session_id, context_type, context_key)
);
```

### 2. Backend Components

#### Session Manager (`session_manager.py`)
- **Session Management**: Create, retrieve, and manage chat sessions
- **Message Persistence**: Store and retrieve conversation history
- **Context Management**: Handle conversation context and user preferences
- **Memory Utilities**: Generate conversation summaries and extract insights

#### Session API (`session_api.py`)
- **REST Endpoints**: Complete API for session management
- **Authentication**: Integrated with existing auth system
- **Error Handling**: Comprehensive error handling and validation

### 3. Frontend Integration

#### Enhanced Chat Interface (`ChatInterface.tsx`)
- **Session Persistence**: localStorage integration for session continuity
- **Automatic Restoration**: Loads chat history on component mount
- **Real-time Sync**: Saves messages to both backend and localStorage
- **Fallback Handling**: Graceful degradation when backend is unavailable

## API Endpoints

### Session Management

#### Get or Create Active Session
```http
GET /api/sessions/active/{user_email}
```

#### Get User Sessions
```http
GET /api/sessions/user/{user_email}?limit=50
```

#### Create New Session
```http
POST /api/sessions/create
Content-Type: application/json

{
  "user_email": "user@example.com",
  "session_name": "Optional Session Name"
}
```

### Message Management

#### Add Message
```http
POST /api/sessions/messages/add
Content-Type: application/json

{
  "session_id": "uuid",
  "message_type": "human|ai|system",
  "content": "Message content",
  "metadata": {"key": "value"},
  "chart_files": ["chart1.html"],
  "query_results": {"data": "results"}
}
```

#### Get Session Messages
```http
GET /api/sessions/messages/{session_id}?limit=100&message_types=human,ai
```

#### Get Recent Messages
```http
GET /api/sessions/messages/recent/{user_email}?hours=24&limit=50
```

### Context Management

#### Set Context
```http
POST /api/sessions/context/set
Content-Type: application/json

{
  "session_id": "uuid",
  "context_type": "user_preference",
  "context_key": "chart_type",
  "context_value": "bar",
  "expires_hours": 168
}
```

#### Get Context
```http
GET /api/sessions/context/{session_id}?context_type=user_preference&context_key=chart_type
```

### Utility Endpoints

#### Get Conversation Summary
```http
GET /api/sessions/conversation-summary/{session_id}?last_n_messages=10
```

#### Get Session Summary
```http
GET /api/sessions/summary/{user_email}
```

#### User Preferences
```http
GET /api/sessions/preferences/{user_email}
POST /api/sessions/preferences/{user_email}
```

## Memory Features

### 1. Conversation Context
- **Previous Messages**: Agents can access conversation history
- **User Intent**: Understanding based on conversation flow
- **Follow-up Queries**: Context-aware responses to related questions

### 2. User Preferences
- **Chart Types**: Remembers preferred visualization styles
- **Query Patterns**: Learns from successful query patterns
- **Response Format**: Adapts to user's preferred response style

### 3. Data Context
- **Recent Queries**: Remembers recent SQL queries and results
- **Chart History**: Tracks generated charts and visualizations
- **Dataset Context**: Maintains context about uploaded datasets

### 4. Session Persistence
- **Browser Refresh**: Chat history survives page reloads
- **Cross-Device**: Sessions accessible across devices (with auth)
- **Long-term Memory**: Conversations stored permanently

## Usage Examples

### Basic Chat with Memory
```javascript
// Frontend automatically loads previous conversation
// User sees full chat history on page load

// User: "Show me sales data"
// AI: "Here's your sales data..." (generates chart)

// User: "Make it a pie chart instead"  
// AI: "I'll convert the previous sales data to a pie chart..." 
// (remembers previous query context)
```

### Context-Aware Responses
```javascript
// Previous conversation about mutual funds
// User: "What about the risk analysis?"
// AI: "Based on our previous discussion about mutual fund performance, 
//      here's the risk analysis for the schemes we looked at..."
```

### User Preference Learning
```javascript
// User consistently asks for bar charts
// System learns preference and suggests bar charts by default
// User: "Show portfolio performance"
// AI: "Here's your portfolio performance as a bar chart (your preferred format)..."
```

## Configuration

### Environment Variables
```bash
# Database connection for session storage
DB_HOST=localhost
DB_PORT=5432
DB_NAME=portfoliosql
DB_USER=your_user
DB_PASSWORD=your_password

# Session configuration
SESSION_TIMEOUT_HOURS=168  # 1 week default
CONTEXT_CLEANUP_INTERVAL=3600  # 1 hour
```

### Frontend Configuration
```typescript
// localStorage keys
const SESSION_STORAGE_KEY = 'chatfolio_session';
const MESSAGES_STORAGE_KEY = 'chatfolio_messages';

// Session persistence settings
const AUTO_SAVE_INTERVAL = 5000; // 5 seconds
const MAX_STORED_MESSAGES = 1000;
const SESSION_EXPIRY_DAYS = 30;
```

## Performance Optimizations

### 1. Database Indexes
- Session lookup by user and activity status
- Message retrieval by session and timestamp
- Context queries by type and expiration

### 2. Caching Strategy
- In-memory caching of active sessions
- localStorage for frontend persistence
- Lazy loading of conversation history

### 3. Cleanup Processes
- Automatic expiration of temporary contexts
- Periodic cleanup of old sessions
- Compression of large conversation histories

## Security Considerations

### 1. Data Privacy
- User data isolation per session
- Encrypted sensitive context data
- Automatic cleanup of expired data

### 2. Authentication
- JWT token validation for all endpoints
- User-specific session access control
- Rate limiting on session creation

### 3. Data Retention
- Configurable retention policies
- User-initiated data deletion
- GDPR compliance features

## Monitoring & Analytics

### 1. Session Metrics
- Active sessions per user
- Average session duration
- Message frequency patterns

### 2. Memory Usage
- Context storage utilization
- Conversation history growth
- Cleanup effectiveness

### 3. Performance Metrics
- Query response times with memory
- Frontend load times
- Database query performance

## Troubleshooting

### Common Issues

#### Session Not Persisting
```bash
# Check database connection
curl -X GET "http://localhost:8001/api/sessions/active/user@example.com"

# Verify localStorage
console.log(localStorage.getItem('chatfolio_session'));
```

#### Memory Context Not Working
```bash
# Check context storage
curl -X GET "http://localhost:8001/api/sessions/context/{session_id}"

# Verify context expiration
# Contexts may have expired - check expires_at timestamps
```

#### Frontend Not Loading History
```javascript
// Check browser console for errors
// Verify authentication token
// Check network requests in DevTools
```

### Database Maintenance
```sql
-- Clean expired contexts
DELETE FROM conversation_contexts 
WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- Archive old sessions
UPDATE chat_sessions 
SET is_active = FALSE 
WHERE updated_at < NOW() - INTERVAL '30 days';
```

## Future Enhancements

### 1. Advanced Memory Features
- Semantic search over conversation history
- Automatic context extraction from conversations
- Cross-session learning and insights

### 2. Enhanced Analytics
- User behavior pattern analysis
- Conversation quality metrics
- Predictive context suggestions

### 3. Integration Improvements
- Real-time collaboration features
- Advanced export/import capabilities
- Third-party integrations (Slack, Teams, etc.)

## Conclusion

The comprehensive memory and session management system transforms the SQL Agent from a stateless query processor into an intelligent, context-aware assistant that learns and adapts to user needs. This foundation enables more natural conversations, better user experience, and powerful analytical capabilities.

The system is designed for scalability, security, and performance, making it suitable for both development and production environments.
