# Multi-Tenant SQL Agent - Frontend

A modern, responsive React/Next.js frontend for the Multi-Tenant SQL Agent system. Provides an intuitive interface for uploading data, managing databases, and querying data using natural language.

## 🚀 Features

### User Interface
- **Modern Design**: Clean, responsive UI built with Tailwind CSS
- **Dark/Light Mode**: Adaptive theme support
- **Mobile Responsive**: Optimized for all device sizes
- **Real-time Updates**: Live query results and status updates

### Core Functionality
- **Session Management**: Create and manage user sessions
- **File Upload**: Drag-and-drop Excel/CSV file upload with progress tracking
- **Multi-Database Querying**: Switch between personal and shared databases
- **Natural Language Queries**: Intuitive chat-like interface for SQL queries
- **Query History**: View and replay previous queries
- **Table Management**: Browse uploaded tables and their schemas

### User Experience
- **Interactive Chat Interface**: ChatGPT-like conversation flow
- **File Preview**: Preview uploaded files before processing
- **Error Handling**: User-friendly error messages and recovery options
- **Loading States**: Smooth loading animations and progress indicators
- **Keyboard Shortcuts**: Quick actions with keyboard navigation

## 🛠️ Tech Stack

### Core Framework
- **Next.js 15.3.4**: React framework with App Router
- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development

### Styling & UI
- **Tailwind CSS 4**: Utility-first CSS framework
- **Lucide React**: Beautiful, customizable icons
- **CSS Modules**: Component-scoped styling

### Data & API
- **Axios**: HTTP client for API communication
- **React Dropzone**: File upload with drag-and-drop
- **SWR/React Query**: Data fetching and caching (if implemented)

### Development Tools
- **ESLint**: Code linting and formatting
- **TypeScript**: Static type checking
- **Turbopack**: Fast development bundler

## 📋 Prerequisites

### Required Software
- Node.js 18+ (LTS recommended)
- npm, yarn, pnpm, or bun
- Backend API server running on port 8001

### Backend Dependency
The frontend requires the Multi-Tenant SQL Agent backend to be running:
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

## 🛠️ Installation

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Dependencies
```bash
# Using npm
npm install

# Using yarn
yarn install

# Using pnpm
pnpm install

# Using bun
bun install
```

### 3. Environment Configuration (Optional)
Create a `.env.local` file for environment-specific settings:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=SQL Agent
NEXT_PUBLIC_VERSION=4.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_DEBUG=false
NEXT_PUBLIC_MAX_FILE_SIZE=10485760
```

## 🚀 Running the Application

### Development Mode
```bash
# Using npm
npm run dev

# Using yarn
yarn dev

# Using pnpm
pnpm dev

# Using bun
bun dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Auto-reload**: Changes are reflected instantly

### Production Build
```bash
# Build the application
npm run build

# Start production server
npm start
```

### Linting
```bash
# Run ESLint
npm run lint

# Fix linting issues
npm run lint --fix
```

## 🏗️ Project Structure

```
frontend/
├── README.md                   # This file
├── package.json               # Dependencies and scripts
├── next.config.ts             # Next.js configuration
├── tsconfig.json              # TypeScript configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── eslint.config.mjs          # ESLint configuration
├── postcss.config.mjs         # PostCSS configuration
├── .gitignore                 # Git ignore rules
├── .next/                     # Next.js build output
├── node_modules/              # Dependencies
├── public/                    # Static assets
│   ├── favicon.ico
│   ├── images/
│   └── icons/
└── src/                       # Source code
    └── app/                   # App Router structure
        ├── layout.tsx         # Root layout
        ├── page.tsx           # Home page
        ├── globals.css        # Global styles
        └── favicon.ico        # App icon
```

## 🎨 UI Components & Features

### Main Interface (`src/app/page.tsx`)
- **Session Creation**: Initialize new user sessions
- **File Upload Zone**: Drag-and-drop file upload with validation
- **Query Interface**: Natural language query input
- **Results Display**: Formatted query results and responses
- **Database Selector**: Switch between available databases
- **Database Browser**: Explore tables and schemas
- **Query History**: Browse and replay previous queries
- **Admin Features**: Session management and monitoring

### Key UI Components

#### File Upload Component
```typescript
// Features:
- Drag-and-drop functionality
- File type validation (.xlsx, .csv)
- Upload progress tracking
- Error handling and retry
- Multiple file support
```

#### Query Interface
```typescript
// Features:
- Chat-like message interface
- Syntax highlighting for SQL
- Query suggestions
- Auto-complete functionality
- Response formatting
```

#### Database Selector
```typescript
// Features:
- Switch between user and portfolio databases
- Real-time database status
- Table count and information
- Connection status indicators
```

## 🔧 Configuration

### Next.js Configuration (`next.config.ts`)
```typescript
const nextConfig = {
  experimental: {
    turbo: true, // Enable Turbopack for faster builds
  },
  images: {
    domains: ['localhost'], // Add allowed image domains
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
}
```

### Tailwind Configuration
```javascript
// Custom theme, colors, and utilities
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {...},
        secondary: {...},
      },
    },
  },
  plugins: [],
}
```

### TypeScript Configuration
- Strict mode enabled
- Path mapping for clean imports
- Next.js optimizations
- ESLint integration

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Mobile Features
- Touch-optimized interface
- Swipe gestures for navigation
- Responsive file upload
- Collapsible sidebar
- Mobile-first design approach

## 🔌 API Integration

### API Client Configuration
```typescript
// axios configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Key API Endpoints Used
- `POST /session/new` - Create user session
- `POST /query` - Submit natural language queries
- `POST /upload` - Upload files
- `GET /user/{id}/tables` - Get user tables
- `GET /user/{id}/databases` - Get available databases
- `GET /user/{id}/history` - Get query history

### Error Handling
- Network error recovery
- API timeout handling
- User-friendly error messages
- Retry mechanisms
- Offline state detection

## 🧪 Testing

### Development Testing
```bash
# Start backend server
cd .. && python start_multitenant.py

# Start frontend in another terminal
npm run dev

# Test workflow:
# 1. Create new session
# 2. Upload test Excel file
# 3. Submit natural language query
# 4. Verify results display
```

### Manual Testing Checklist
- [ ] Session creation and management
- [ ] File upload (Excel/CSV)
- [ ] Multi-sheet file handling
- [ ] Natural language queries
- [ ] Database switching
- [ ] Error handling
- [ ] Mobile responsiveness
- [ ] Browser compatibility

## 🎯 Performance Optimization

### Build Optimization
- **Turbopack**: Faster development builds
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Automatic font loading
- **Bundle Analysis**: webpack-bundle-analyzer

### Runtime Performance
- **React 19 Features**: Concurrent rendering
- **Lazy Loading**: Component and route lazy loading
- **Memoization**: React.memo and useMemo
- **Virtual Scrolling**: For large data sets
- **Debounced Inputs**: Optimized search and queries

## 🔒 Security Considerations

### Client-Side Security
- **Input Validation**: Client-side validation for all inputs
- **XSS Prevention**: Sanitized user content
- **CSRF Protection**: Token-based protection
- **File Upload Security**: Type and size validation
- **Environment Variables**: Secure API key handling

### Data Handling
- **No Sensitive Data Storage**: No API keys in client code
- **Session Management**: Secure session handling
- **File Processing**: Client-side file validation
- **Error Messages**: No sensitive information exposure

## 🚨 Troubleshooting

### Common Issues

#### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8001/health

# Check network connectivity
ping localhost

# Verify API endpoints
curl http://localhost:8001/docs
```

#### Build Issues
```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules
rm -rf node_modules && npm install

# Check Node.js version
node --version  # Should be 18+
```

#### Development Server Issues
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Start with different port
npm run dev -- -p 3001
```

### Browser Compatibility
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

### Performance Issues
- Check browser developer tools
- Monitor network requests
- Analyze bundle size
- Profile React components

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_APP_NAME=SQL Agent
NODE_ENV=production
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow ESLint configuration
- Use TypeScript for type safety
- Follow React best practices
- Use Tailwind for styling
- Write meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For frontend-specific issues:
1. Check browser console for errors
2. Verify backend API connectivity
3. Review network requests in DevTools
4. Check this README for troubleshooting
5. Create an issue in the repository

## 🔄 Version History

- **v4.0**: Multi-tenant frontend with enhanced UI
- **v3.0**: React/Next.js implementation
- **v2.0**: Basic web interface
- **v1.0**: CLI-only interface

## 🎨 Design System

### Colors
- **Primary**: Blue tones for main actions
- **Secondary**: Gray tones for secondary elements
- **Success**: Green for successful operations
- **Warning**: Yellow for warnings
- **Error**: Red for errors

### Typography
- **Headings**: Inter font family
- **Body**: System font stack
- **Code**: Fira Code monospace

### Components
- **Buttons**: Consistent styling with hover states
- **Forms**: Accessible form controls
- **Cards**: Consistent card layout
- **Modals**: Accessible modal dialogs
