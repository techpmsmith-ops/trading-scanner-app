const browserApiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const serverApiBase = process.env.API_INTERNAL_BASE_URL || browserApiBase;
const API_BASE = (typeof window === "undefined" ? serverApiBase : browserApiBase).trim().replace(/\/$/, "");

export type ScanResult = {
  id: number;
  scan_run_id: number;
  ticker_id: number;
  symbol: string;
  close_price: number;
  score_total: number;
  score_trend: number;
  score_momentum: number;
  score_volume: number;
  score_risk: number;
  score_setup_quality: number;
  setup_types: string[];
  risk_flags: string[];
  indicators: Record<string, number | string | null>;
  entry_zone: number | null;
  stop_loss: number | null;
  target_1: number | null;
  target_2: number | null;
  risk_reward: number | null;
  explanation: string;
  created_at: string;
};

export type ScanRun = {
  id: number;
  run_date: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  universe_count: number;
  result_count: number;
  duration_seconds: number | null;
  results: ScanResult[];
};

export type ScanStatus = {
  latest_run: Omit<ScanRun, "results"> | null;
  last_successful_scan: Omit<ScanRun, "results"> | null;
  running: boolean;
};

export type PriceBar = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adjusted_close: number;
  volume: number;
};

export type JournalEntry = {
  id: number;
  symbol: string;
  setup_type: string;
  direction: "long" | "short" | "watchlist";
  status: "planned" | "open" | "closed" | "skipped";
  planned_entry: number | null;
  actual_entry: number | null;
  stop_loss: number | null;
  target_1: number | null;
  target_2: number | null;
  exit_price: number | null;
  position_size: number | null;
  risk_amount: number | null;
  pnl_amount: number | null;
  pnl_percent: number | null;
  result: string | null;
  entry_date: string | null;
  exit_date: string | null;
  notes: string | null;
  emotions: string | null;
  mistake_tags: string[] | null;
  lesson_learned: string | null;
  linked_scan_result_id: number | null;
  created_at: string;
  updated_at: string;
};

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const clientToken = clientAuthToken();
  if (clientToken && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${clientToken}`);
  const response = await fetch(`${API_BASE}${normalizedPath}`, {
    ...options,
    headers,
    cache: "no-store"
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

function clientAuthToken() {
  if (typeof document === "undefined") return "";
  const token = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith("scanner_token="))
    ?.split("=")[1];
  return token ? decodeURIComponent(token) : "";
}

export function currency(value?: number | null) {
  if (value === null || value === undefined) return "-";
  return `$${value.toFixed(2)}`;
}

export function number(value?: number | string | null, digits = 2) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "string") return value;
  return value.toFixed(digits);
}

export function dateTime(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}
