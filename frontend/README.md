# Sherify Frontend — Campaign Manager Dashboard

Modern, responsive, production-grade SaaS web dashboard for **Sherify Automated Mass Campaign Manager**, built with React 18, TypeScript, Vite, TanStack Query, and Tailwind CSS.

---

## 🚀 Features

- **Authentication & Security**: JWT bearer token authentication, login, registration, session persistence, automatic 401 redirect.
- **Audience & Contact List Management**:
  - Create and manage contact lists.
  - List and search subscribers with status filters (`active`, `unsubscribed`, `bounced`).
  - Add individual subscribers with optional JSON metadata.
  - **Bulk CSV Import (V4)**: Streaming CSV file upload with real-time polling progress, summary metrics (imported, duplicate, invalid rows), and paginated row-level error log inspection.
- **Email Template Engine (V2)**:
  - Compose HTML and plain text email templates.
  - Live **Sandboxed Safe Preview** isolating user HTML inside a secure iframe (`sandbox=""`).
  - Referential integrity protection preventing deletion of referenced templates.
- **Campaign State Machine & Dispatch (V2 + V3)**:
  - Create campaigns selecting from available contact lists and templates.
  - Status progression: `DRAFT` → `READY` → `QUEUED` → `SENDING` → `COMPLETED` / `FAILED`.
  - Validate and transition to `READY`.
  - Dispatch campaigns with confirmation modal (`HTTP 202 Accepted`).
  - Real-time status tracker auto-polling until terminal delivery state.
- **Durable Campaign Analytics & Tracking (V5)**:
  - Per-campaign analytics dashboard consuming SQL-aggregated stats.
  - KPI cards: Total Recipients Snapshot, Sent/Delivered Count, Delivery Failures, Bounced Emails (Provider Webhook), and Unique Opens.
  - Visual delivery status progress bars and Engagement open rate progression.
- **Settings & Connectivity Diagnostics**:
  - Authenticated user profile information.
  - Live system connectivity diagnostics against backend `/health` and PostgreSQL database.

---

## 🛠️ Technology Stack

- **Framework**: [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Routing**: [React Router 6](https://reactrouter.com/)
- **Server State & Caching**: [TanStack Query v5](https://tanstack.com/query)
- **HTTP Client**: [Axios](https://axios-http.com/) with request/response interceptors and error normalization
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Testing**: [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/)

---

## 📁 Directory Structure

```
frontend/
├── src/
│   ├── api/                  # Centralized Axios client & API services
│   │   ├── client.ts         # Axios instance, interceptors, error normalizer
│   │   ├── auth.ts           # Login, register, current user
│   │   ├── contactLists.ts   # Contact list CRUD
│   │   ├── subscribers.ts    # Subscriber CRUD & CSV import
│   │   ├── templates.ts      # Template CRUD
│   │   ├── campaigns.ts      # Campaign CRUD, ready, send, stats
│   │   ├── imports.ts        # Import job status & errors
│   │   └── health.ts         # System health check
│   ├── components/
│   │   ├── common/           # Button, Input, Select, Modal, Badge, Pagination, Skeleton, EmptyState, Alert, SafeHtmlPreview
│   │   └── layout/           # AppLayout, Sidebar, Header
│   ├── context/
│   │   └── AuthContext.tsx   # Authentication provider and session state
│   ├── pages/
│   │   ├── auth/             # LoginPage, RegisterPage
│   │   ├── dashboard/        # DashboardPage
│   │   ├── contacts/         # ContactListsPage, ContactListDetailPage
│   │   ├── templates/        # TemplatesPage, TemplateCreatePage, TemplateEditPage
│   │   ├── campaigns/        # CampaignsPage, CampaignCreatePage, CampaignDetailPage, CampaignAnalyticsPage
│   │   ├── analytics/        # AnalyticsPage
│   │   ├── settings/         # SettingsPage
│   │   └── NotFoundPage.tsx
│   ├── types/
│   │   └── index.ts          # TypeScript interfaces matching backend models
│   └── test/                 # Vitest test suites
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

---

## 💻 Getting Started

### 1. Prerequisites
- Node.js 18+ (tested on Node 20+)
- npm 9+

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Environment Configuration
Create a `.env` file (copied from `.env.example`):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4. Run Development Server
```bash
npm run dev
```
The application will be accessible at: [http://localhost:3000](http://localhost:3000)

### 5. Run Tests
```bash
npm run test
```

### 6. TypeScript Type Check & Production Build
```bash
npm run typecheck
npm run build
```
Production assets are generated in `dist/`.
