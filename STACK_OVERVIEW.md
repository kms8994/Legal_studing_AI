# Stack Overview

## Frontend

- Next.js 16
- React 18
- TypeScript
- Tailwind CSS
- React Flow (`@xyflow/react`)
  - Diagram node and edge rendering
- ELK.js
  - Automatic vertical diagram layout
- Vercel
  - Frontend hosting
  - `/api/*` proxy to the backend

## Backend

- Python 3
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv
- pypdf
  - PDF text extraction
- systemd
  - Keeps the backend service running on the VM

## AI And Analysis

- Google Gemini API
- Model
  - `gemini-3-flash-preview`
- IRAC-based analysis structure
- Expert-mode diagram generation
  - Party relationship
  - Event timeline
  - Legal reasoning structure
- Dictionary-based legal term explanations
- Statute/article reference extraction and hyperlink generation

## Legal Data And External APIs

- National Law Information Center Open API
  - `lawSearch.do`
  - `lawService.do`
  - `target=prec`: case search and case detail lookup
  - `target=law`: statute search
  - `target=lawjosub`: statute article lookup
- Fallback behavior
  - If the official API has metadata but no case body, the app analyzes the uploaded PDF or entered text.

## Deployment And Infrastructure

- GitHub
  - Source repository
  - Deployment trigger
- Vercel
  - Frontend deployment
- Google Cloud Compute Engine
  - Backend VM
- Ubuntu 22.04 LTS
- Backend service
  - `systemd` service: `legal-ai-backend`
- Backend base URL
  - `http://35.224.14.137:8000`

## Environment Variables

### Vercel

```env
NEXT_PUBLIC_API_BASE_URL=/api
BACKEND_API_ORIGIN=http://35.224.14.137:8000
```

### Backend VM

```env
APP_ENV=production
APP_NAME=Case AI Learning Service
BACKEND_CORS_ORIGINS=*
LAWINFO_API_KEY=...
LAWINFO_BASE_URL=http://www.law.go.kr/DRF
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
```

## Diagram Stack

### Previous

- Mermaid

### Current

- React Flow
- ELK.js

### Reason For Change

- Better node and edge control
- More reliable arrow rendering
- Zoom and pan support
- Easier responsive layout control
- Better fit for complex legal relationships and procedural diagrams

