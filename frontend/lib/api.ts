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

export type DailyRecommendation = {
  id: number;
  recommendation_date: string;
  scan_run_id: number;
  scan_result_id: number;
  symbol: string;
  rank: number;
  score_total: number;
  setup_types: string[];
  risk_flags: string[];
  rationale: string;
  disclaimer: string;
  created_at: string;
};

export type WeeklyPrediction = {
  id: number;
  week_start: string;
  week_end: string;
  symbol: string;
  scan_run_id: number | null;
  scan_result_id: number | null;
  direction: string;
  predicted_return_pct: number;
  confidence: number;
  score_total: number;
  component_scores: Record<string, number>;
  rationale: string;
  status: string;
  start_price: number | null;
  end_price: number | null;
  actual_return_pct: number | null;
  outcome: string | null;
  outcome_reason: string | null;
  false_positive: boolean;
  news_sentiment_score: number | null;
  news_sentiment_label: string | null;
  created_at: string;
  evaluated_at: string | null;
};

export type ScoringWeight = {
  id: number;
  effective_date: string;
  weights: Record<string, number>;
  reason: string;
  created_at: string;
};

export type WeeklyEvaluationReport = {
  id: number;
  week_start: string;
  week_end: string;
  evaluated_count: number;
  accuracy: number;
  wins: number;
  losses: number;
  win_loss_ratio: number | null;
  false_positives: number;
  indicator_effectiveness: Record<string, Record<string, number>>;
  news_sentiment_correlation: {
    sample_size?: number;
    aligned_count?: number;
    alignment_rate?: number;
    average_sentiment_score?: number;
    by_symbol?: Record<string, { score: number | null; label: string | null; outcome: string | null }>;
  };
  market_conditions: Record<string, any>;
  weight_changes: Record<string, any>;
  confidence_notes: string;
  created_at: string;
};

export type AlertSubscription = {
  id: number;
  channel: "telegram" | "sms";
  destination_label: string | null;
  enabled: boolean;
  alert_types: string[];
  created_at: string;
  updated_at: string;
};

export type Phase2Dashboard = {
  daily_top_five: DailyRecommendation[];
  weekly_predictions: WeeklyPrediction[];
  scoring_weights: ScoringWeight | null;
  latest_evaluation: WeeklyEvaluationReport | null;
  prediction_symbols: string[];
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
