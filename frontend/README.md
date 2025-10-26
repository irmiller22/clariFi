# clariFi Frontend

The frontend for clariFi, a personal finance application for analyzing credit card spending patterns via CSV uploads.

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API server running (see `../backend/README.md`)

### Environment Variables

Create a `.envrc` file in the frontend directory with the following variables:

```bash
# Backend API URL for server-side API routes (Next.js API routes)
export BACKEND_URL=http://127.0.0.1:8000

# Frontend client API URL (must be NEXT_PUBLIC_ for client-side access)
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

**Environment Variable Explanation:**

- `BACKEND_URL`: Used by Next.js API routes (server-side) to proxy requests to the FastAPI backend
- `NEXT_PUBLIC_API_URL`: Used by client-side code for direct API calls to the backend

**Note:** The `.envrc` file is gitignored for security. Copy the example above and adjust URLs as needed for your environment.

### Installation & Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## Features

- **CSV Upload**: Drag-and-drop interface for uploading bank CSV files
- **Transaction Management**: View, search, filter, and sort transactions
- **Analytics Dashboard**: Interactive charts and financial summaries
- **Dark/Light Mode**: Theme toggle with system preference detection
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Charts**: Recharts
- **Icons**: Lucide React
- **UI Components**: Radix UI primitives

## API Integration

The frontend communicates with the FastAPI backend through:

1. **Next.js API Routes** (`/app/api/`): Server-side proxy routes that forward requests to the backend
2. **Direct API Calls**: Client-side calls to the backend for real-time interactions

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── api/               # API route handlers (proxy to backend)
│   ├── globals.css        # Global styles and theme variables
│   ├── layout.tsx         # Root layout component
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── analytics-dashboard.tsx
│   ├── theme-toggle.tsx
│   ├── transaction-table.tsx
│   └── upload-zone.tsx
├── hooks/                 # Custom React hooks
│   └── use-theme.ts
├── lib/                   # Utilities and types
│   ├── api.ts            # API client functions
│   ├── types.ts          # TypeScript type definitions
│   └── utils.ts          # Utility functions
└── public/               # Static assets
```

## Development

The page auto-updates as you edit files. Key files to modify:

- `app/page.tsx` - Main application page
- `components/` - React components
- `lib/types.ts` - TypeScript interfaces
- `app/globals.css` - Styling and theme

## Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start
```

For deployment, ensure environment variables are properly configured for your production backend URL.
