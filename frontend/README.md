# ⚛️ PayShield AI — Frontend Guide

## Stack
- **Framework:** React 18 + Vite + TypeScript
- **Styling:** Tailwind CSS
- **State:** React Query (server state) + useState/useContext (local state)
- **HTTP Client:** Axios
- **Charts:** Recharts (risk visualization)
- **Forms:** React Hook Form + Zod

---

## Table of Contents
1. [Project Setup](#1-project-setup)
2. [Directory Structure](#2-directory-structure)
3. [Dependencies](#3-dependencies)
4. [TypeScript Types](#4-typescript-types)
5. [API Hooks](#5-api-hooks)
6. [Biometric Capture Hook](#6-biometric-capture-hook)
7. [Pages](#7-pages)
8. [Core Components](#8-core-components)
9. [Routing](#9-routing)
10. [Environment Config](#10-environment-config)

---

## 1. Project Setup

```bash
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

App runs at: http://localhost:5173

**Build for production:**
```bash
npm run build
npm run preview
```

---

## 2. Directory Structure

```
frontend/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── pages/
    │   ├── OnboardingPage.tsx       ← Registration + biometric capture
    │   ├── DashboardPage.tsx        ← Analyst main dashboard
    │   └── ReviewQueuePage.tsx      ← REVIEW state queue
    ├── components/
    │   ├── RiskMeter.tsx            ← Visual risk gauge
    │   ├── AgentBreakdown.tsx       ← Per-agent score cards
    │   ├── DecisionBadge.tsx        ← APPROVE/REVIEW/REJECT badge
    │   ├── AnalystOverride.tsx      ← Human override form
    │   ├── BiometricCapture.tsx     ← Invisible biometric recorder
    │   └── FlagList.tsx             ← Risk flag tags
    ├── hooks/
    │   ├── useBiometrics.ts         ← Keystroke + mouse signal collection
    │   └── useRiskAssessment.ts     ← API submission hook
    └── types/
        └── risk.types.ts            ← All TypeScript interfaces
```

---

## 3. Dependencies

**`package.json` (key dependencies)**
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "axios": "^1.7.2",
    "@tanstack/react-query": "^5.40.0",
    "react-hook-form": "^7.51.5",
    "zod": "^3.23.8",
    "@hookform/resolvers": "^3.6.0",
    "recharts": "^2.12.7",
    "tailwindcss": "^3.4.4",
    "lucide-react": "^0.395.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.2.13",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}
```

**Install command:**
```bash
npm install react react-dom react-router-dom axios @tanstack/react-query react-hook-form zod @hookform/resolvers recharts tailwindcss lucide-react
npm install -D @types/react @types/react-dom @vitejs/plugin-react typescript vite autoprefixer postcss
```

---

## 4. TypeScript Types

**`src/types/risk.types.ts`**

```typescript
// ── Submission ────────────────────────────────────────────────────

export interface UserInput {
  full_name: string;
  email: string;
  phone: string;
  date_of_birth?: string;
  address?: string;
  country?: string;
  ktp_number?: string;
}

export interface CompanyInput {
  name?: string;
  registration_number?: string;
}

export interface BiometricInput {
  typing_cadence_ms: number[];
  mouse_entropy_score: number;
  session_duration_sec: number;
  navigation_path: string[];
}

export interface DeviceInput {
  ip_address: string;
  user_agent: string;
  device_fingerprint: string;
}

export interface ApplicationSubmitRequest {
  user: UserInput;
  company?: CompanyInput;
  biometrics?: BiometricInput;
  device: DeviceInput;
  ktp_image_base64?: string;
  selfie_image_base64?: string;
}

// ── Response ─────────────────────────────────────────────────────

export type DecisionType = 'APPROVE' | 'REVIEW' | 'REJECT';

export interface AgentDetail {
  score: number;
  flags: string[];
  explanation?: string;
}

export interface ApplicationResponse {
  application_id: string;
  identity_risk: number;
  behavior_risk: number;
  network_risk: number;
  overall_risk: number;
  decision: DecisionType;
  confidence: number;
  explanation: string;
  agent_details: {
    identity: AgentDetail;
    behavioral: AgentDetail;
    network: AgentDetail;
  };
}

// ── Review Queue ─────────────────────────────────────────────────

export interface ReviewQueueItem {
  application_id: string;
  full_name: string;
  email: string;
  overall_risk: number;
  identity_risk: number;
  behavior_risk: number;
  network_risk: number;
  confidence: number;
  decision: DecisionType;
  explanation: string;
  flags: string[];
  created_at: string;
}

// ── Analyst Override ─────────────────────────────────────────────

export type HumanDecision = 'CONFIRMED_FRAUD' | 'CLEARED' | 'NEEDS_MORE_INFO';

export interface AnalystOverrideRequest {
  application_id: string;
  human_decision: HumanDecision;
  analyst_note?: string;
  analyst_id?: string;
}

// ── Dashboard Stats ──────────────────────────────────────────────

export interface DashboardStats {
  total_applications: number;
  approved: number;
  review: number;
  rejected: number;
  override_count: number;
  avg_risk_score: number;
}
```

---

## 5. API Hooks

**`src/hooks/useRiskAssessment.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import type {
  ApplicationSubmitRequest,
  ApplicationResponse,
  ReviewQueueItem,
  AnalystOverrideRequest,
  DashboardStats
} from '../types/risk.types';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE });

// Submit new application for risk assessment
export function useSubmitApplication() {
  return useMutation<ApplicationResponse, Error, ApplicationSubmitRequest>({
    mutationFn: (payload) =>
      api.post('/api/v1/applications/submit', payload).then(r => r.data),
  });
}

// Fetch review queue
export function useReviewQueue() {
  return useQuery<ReviewQueueItem[]>({
    queryKey: ['review-queue'],
    queryFn: () => api.get('/api/v1/decisions/review-queue').then(r => r.data),
    refetchInterval: 30_000, // Poll every 30s
  });
}

// Fetch dashboard stats
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/api/v1/analyst/stats').then(r => r.data),
    refetchInterval: 60_000,
  });
}

// Submit analyst override
export function useAnalystOverride() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, AnalystOverrideRequest>({
    mutationFn: (payload) =>
      api.post('/api/v1/analyst/override', payload).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });
}
```

---

## 6. Biometric Capture Hook

**`src/hooks/useBiometrics.ts`**

```typescript
import { useState, useRef, useCallback, useEffect } from 'react';
import type { BiometricInput } from '../types/risk.types';

interface MousePoint { x: number; y: number }

function shannonEntropy(points: MousePoint[]): number {
  if (points.length < 2) return 0.5;
  const vectors = points.slice(1).map((p, i) => ({
    dx: p.x - points[i].x,
    dy: p.y - points[i].y,
  }));
  const angles = vectors.map(v => Math.atan2(v.dy, v.dx));
  const buckets: Record<number, number> = {};
  const BUCKETS = 8;
  angles.forEach(a => {
    const bucket = Math.floor(((a + Math.PI) / (2 * Math.PI)) * BUCKETS);
    buckets[bucket] = (buckets[bucket] ?? 0) + 1;
  });
  const total = angles.length;
  return -Object.values(buckets).reduce((sum, count) => {
    const p = count / total;
    return sum + (p > 0 ? p * Math.log2(p) : 0);
  }, 0) / Math.log2(BUCKETS); // Normalized 0-1
}

export function useBiometrics() {
  const [keystrokeTimes, setKeystrokeTimes] = useState<number[]>([]);
  const [mousePoints, setMousePoints] = useState<MousePoint[]>([]);
  const [navigationPath, setNavigationPath] = useState<string[]>(['home']);
  const sessionStart = useRef(Date.now());
  const lastKeyTime = useRef<number | null>(null);

  const handleKeyDown = useCallback(() => {
    const now = Date.now();
    if (lastKeyTime.current !== null) {
      setKeystrokeTimes(prev => [...prev, now - lastKeyTime.current!]);
    }
    lastKeyTime.current = now;
  }, []);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    setMousePoints(prev => {
      if (prev.length > 100) return prev; // Cap at 100 points
      return [...prev, { x: e.clientX, y: e.clientY }];
    });
  }, []);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [handleKeyDown, handleMouseMove]);

  const trackPage = useCallback((page: string) => {
    setNavigationPath(prev => [...prev, page]);
  }, []);

  const collect = useCallback((): BiometricInput => ({
    typing_cadence_ms: keystrokeTimes,
    mouse_entropy_score: shannonEntropy(mousePoints),
    session_duration_sec: Math.floor((Date.now() - sessionStart.current) / 1000),
    navigation_path: navigationPath,
  }), [keystrokeTimes, mousePoints, navigationPath]);

  return { trackPage, collect };
}
```

---

## 7. Pages

### `OnboardingPage.tsx` — Responsibilities
- Render multi-step registration form
- Steps: (1) Personal Info → (2) KTP / Identity Docs → (3) Company Info → (4) Submit
- Attach `useBiometrics` hook invisibly to capture signals during form fill
- On submit: collect biometrics, build `ApplicationSubmitRequest`, call `useSubmitApplication`
- On success: navigate to result page showing `DecisionBadge` + `AgentBreakdown`

**Key state:**
```typescript
const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
const [ktpFile, setKtpFile] = useState<string | null>(null);    // base64
const [selfieFile, setSelfieFile] = useState<string | null>(null); // base64
const { collect, trackPage } = useBiometrics();
const { mutate: submit, isPending, data: result, isError } = useSubmitApplication();
```

**File to base64 conversion:**
```typescript
const toBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
```

---

### `DashboardPage.tsx` — Responsibilities
- Display `DashboardStats` summary cards (Total / Approved / Review / Rejected)
- Show recent decision history table
- Display average risk score gauge
- Link to Review Queue

---

### `ReviewQueuePage.tsx` — Responsibilities
- Fetch and display `ReviewQueueItem[]`
- Each row expands to show full risk breakdown
- Render `AgentBreakdown` cards
- Render `AnalystOverride` form per item

---

## 8. Core Components

### `RiskMeter.tsx`
Displays a visual gauge for a risk score (0–1).

```tsx
import { PieChart, Pie, Cell } from 'recharts';

interface RiskMeterProps {
  score: number;         // 0.0 - 1.0
  label?: string;
  size?: number;
}

const colorFromScore = (score: number) =>
  score < 0.3 ? '#22c55e' : score < 0.7 ? '#f59e0b' : '#ef4444';

export function RiskMeter({ score, label = 'Risk Score', size = 120 }: RiskMeterProps) {
  const data = [{ value: score }, { value: 1 - score }];
  const color = colorFromScore(score);
  return (
    <div className="flex flex-col items-center gap-1">
      <PieChart width={size} height={size / 2 + 10}>
        <Pie
          data={data}
          cx={size / 2}
          cy={size / 2}
          startAngle={180}
          endAngle={0}
          innerRadius={size * 0.3}
          outerRadius={size * 0.45}
          dataKey="value"
        >
          <Cell fill={color} />
          <Cell fill="#e5e7eb" />
        </Pie>
      </PieChart>
      <span className="text-lg font-bold" style={{ color }}>{(score * 100).toFixed(0)}%</span>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
}
```

---

### `DecisionBadge.tsx`

```tsx
import type { DecisionType } from '../types/risk.types';

const styles: Record<DecisionType, string> = {
  APPROVE: 'bg-green-100 text-green-800 border border-green-300',
  REVIEW:  'bg-yellow-100 text-yellow-800 border border-yellow-300',
  REJECT:  'bg-red-100 text-red-800 border border-red-300',
};

const icons: Record<DecisionType, string> = {
  APPROVE: '✅',
  REVIEW: '⚠️',
  REJECT: '🚫',
};

export function DecisionBadge({ decision }: { decision: DecisionType }) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${styles[decision]}`}>
      {icons[decision]} {decision}
    </span>
  );
}
```

---

### `AgentBreakdown.tsx`

```tsx
import { RiskMeter } from './RiskMeter';
import { FlagList } from './FlagList';
import type { ApplicationResponse } from '../types/risk.types';

export function AgentBreakdown({ data }: { data: ApplicationResponse }) {
  const agents = [
    { label: 'Identity Risk', score: data.identity_risk, detail: data.agent_details.identity },
    { label: 'Behavioral Risk', score: data.behavior_risk, detail: data.agent_details.behavioral },
    { label: 'Network Risk', score: data.network_risk, detail: data.agent_details.network },
  ];
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {agents.map(agent => (
        <div key={agent.label} className="bg-white rounded-xl shadow p-4 flex flex-col items-center gap-3">
          <h3 className="font-semibold text-gray-700 text-sm">{agent.label}</h3>
          <RiskMeter score={agent.score} label={agent.label} size={100} />
          <FlagList flags={agent.detail.flags} />
        </div>
      ))}
    </div>
  );
}
```

---

### `AnalystOverride.tsx`

```tsx
import { useState } from 'react';
import { useAnalystOverride } from '../hooks/useRiskAssessment';
import type { HumanDecision } from '../types/risk.types';

interface Props { applicationId: string; onDone: () => void; }

export function AnalystOverride({ applicationId, onDone }: Props) {
  const [decision, setDecision] = useState<HumanDecision>('CLEARED');
  const [note, setNote] = useState('');
  const { mutate: override, isPending } = useAnalystOverride();

  const handleSubmit = () => {
    override(
      { application_id: applicationId, human_decision: decision, analyst_note: note },
      { onSuccess: onDone }
    );
  };

  return (
    <div className="bg-gray-50 border rounded-lg p-4 space-y-3">
      <h4 className="font-semibold text-gray-700">Analyst Decision</h4>
      <select
        className="w-full border rounded px-3 py-2 text-sm"
        value={decision}
        onChange={e => setDecision(e.target.value as HumanDecision)}
      >
        <option value="CLEARED">✅ Clear — Not Fraud</option>
        <option value="CONFIRMED_FRAUD">🚫 Confirm Fraud</option>
        <option value="NEEDS_MORE_INFO">⚠️ Needs More Info</option>
      </select>
      <textarea
        className="w-full border rounded px-3 py-2 text-sm"
        placeholder="Investigation notes (required for fraud confirmation)..."
        rows={3}
        value={note}
        onChange={e => setNote(e.target.value)}
      />
      <button
        className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-semibold disabled:opacity-50"
        onClick={handleSubmit}
        disabled={isPending}
      >
        {isPending ? 'Submitting...' : 'Submit Decision'}
      </button>
    </div>
  );
}
```

---

### `BiometricCapture.tsx`
Invisible component — attach to registration form container to auto-collect signals.

```tsx
import { useEffect } from 'react';
import { useBiometrics } from '../hooks/useBiometrics';

interface Props {
  onCollect: (biometrics: ReturnType<ReturnType<typeof useBiometrics>['collect']>) => void;
}

// This component renders nothing visible.
// Mount it once inside the registration form.
// Call collect() before submission.
export function BiometricCapture() {
  // Capture is handled by useBiometrics hook at the page level.
  // This component serves as a placeholder for documentation clarity.
  return null;
}
```

---

## 9. Routing

**`src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OnboardingPage } from './pages/OnboardingPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/onboarding" replace />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/review-queue" element={<ReviewQueuePage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## 10. Environment Config

**`src/vite.config.ts`**
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

**`.env.local`**
```env
VITE_API_URL=http://localhost:8000
```

In production (Docker), the Nginx reverse proxy handles `/api` routing — `VITE_API_URL` can be left empty.
