import { useCallback, useEffect, useRef, useState } from "react";

/* ---------- types mirrored from the API (src/wfintel/pipeline.py) ---------- */
export interface Provenance {
  run_id: string;
  commit: string;
  dirty: boolean;
  created_at: string;
  runtime_seconds: number;
  python: string;
  packages: Record<string, string>;
  source_sha256: Record<string, string>;
  inputs_sha256: Record<string, string>;
}

export interface Kpis {
  employees: number;
  leavers: number;
  rate: number;
  median_income: number;
  overtime_share: number;
  median_tenure: number;
  median_age: number;
  inconsistent_rows: number;
}

export interface TableCount {
  table_name: string;
  rows: number;
}

export interface Overview {
  kpis: Kpis;
  model_tables: TableCount[];
}

export interface DataCheck {
  id: number;
  check_name: string;
  value: number;
  unit: string;
  action: string;
}

export interface Quality {
  data_checks: DataCheck[];
  model_tables: TableCount[];
}

export interface Level {
  level: string | number;
  label: string;
  employees: number;
  leavers: number;
  rate: number;
  ci_low: number;
  ci_high: number;
}

export interface Factor {
  name: string;
  levels: Level[];
}

export interface TestRow {
  factor: string;
  name: string;
  test: string;
  statistic: number;
  df: number | null;
  p: number;
  p_holm: number;
  significant: boolean;
  effect: number;
  effect_name: string;
  n: number;
  median_left?: number;
  median_stayed?: number;
}

export interface Stratified {
  exposure: string;
  stratum: string;
  crude: { odds_ratio: number; ci: [number, number] };
  mantel_haenszel: { odds_ratio: number; ci: [number, number]; p: number };
  homogeneity_p: number;
  strata: {
    stratum: string;
    employees: number;
    exposed: number;
    rate_exposed: number;
    rate_unexposed: number;
    odds_ratio: number;
    ci: [number, number];
  }[];
}

export interface Attrition {
  factors: Record<string, Factor>;
  tests: TestRow[];
  stratified: Stratified[];
}

export interface RoleRow {
  department: string;
  job_role: string;
  employees: number;
  leavers: number;
  rate: number;
  median_income: number;
  overtime_share: number;
  mean_job_satisfaction: number;
  median_tenure: number;
  mean_job_level: number;
}

export interface Departments {
  departments: RoleRow[];
}

export interface Compensation {
  compensation: {
    job_level: number;
    employees: number;
    leavers: number;
    rate: number;
    median_income: number;
    median_income_stayed: number;
    median_income_left: number;
    overtime_share: number;
    no_stock_share: number;
  }[];
  income_bands: { income_band: number; min_income: number; max_income: number; employees: number; leavers: number; rate: number }[];
  income_by_level: { job_level: number; left: number; incomes: number[] }[];
  stock_by_marital: { marital_status: string; levels: Record<string, number> }[];
}

export interface Tenure {
  tenure_curve: { years: number; employees: number; leavers: number; rate: number }[];
}

export interface Metrics {
  auroc: number;
  average_precision: number;
  brier: number;
  log_loss: number;
  calibration_intercept: number | null;
  calibration_slope: number | null;
}

export interface OddsRatio {
  term: string;
  label: string;
  group: "numeric" | "category";
  odds_ratio: number;
  ci: [number, number];
  p: number;
}

export interface Profile {
  employees: number;
  leavers: number;
  rate: number;
  ci: [number, number];
  median_age: number;
  median_income: number;
  median_tenure: number;
  mean_job_level: number;
  overtime_share: number;
  low_job_satisfaction_share: number;
  frequent_travel_share: number;
  no_stock_share: number;
  departments: Record<string, number>;
}

export interface FairRow {
  attribute: string;
  group: string;
  employees: number;
  leavers: number;
  observed_rate: number;
  mean_predicted: number;
  auroc: number | null;
  flagged_share: number;
  true_positive_rate: number | null;
  false_positive_rate: number | null;
}

export interface Risk {
  model: {
    split: { train: number; test: number; train_leavers: number; test_leavers: number; seed: number };
    c: number;
    c_grid: { c: number; log_loss: number; auroc: number }[];
    test: Record<string, Metrics>;
    bootstrap: {
      models: Record<string, { auroc: [number, number]; average_precision: [number, number]; brier: [number, number] }>;
      auroc_diff_logistic_minus: Record<string, { diff: number; ci: [number, number] }>;
    };
    standardised_coefficients: { term: string; coef: number }[];
    odds_ratios: {
      terms: OddsRatio[];
      reference_levels: Record<string, string>;
      n: number;
      pseudo_r2: number;
      converged: boolean;
      vif: Record<string, number>;
    };
    oof_metrics: Metrics;
    without_stock_options: { test: Metrics; c: number; oof_metrics: Metrics };
    test_size_employees: number;
  };
  risk_segments: { bounds: number[]; bands: (Profile & { band: string; range: [number, number]; mean_predicted: number })[] };
  segments: {
    k: number;
    silhouette: Record<string, number>;
    stability_ari: number[];
    features: string[];
    segments: (Profile & { segment: number; label: string; centre: Record<string, number> })[];
  };
  fairness: FairRow[];
  fairness_without_stock_options: FairRow[];
}

export interface Recommendation {
  area: string;
  title: string;
  finding: string;
  evidence: string[];
  action: string;
  basis: string;
}

export interface Recommendations {
  recommendations: Recommendation[];
}

export interface Audit {
  passed: boolean;
  files: string[];
  rules: string[];
  findings: { file: string; line: number; rule: string; text: string }[];
}

/* ---------- fetching ---------- */
export class ApiError extends Error {
  constructor(
    public url: string,
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const cache = new Map<string, unknown>();

const TOKEN_KEY = "workforce-intel-token";

/** The access token for a server started with WFINTEL_TOKEN, kept for this browser tab only. */
export function getToken(): string {
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setToken(token: string): void {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the token is not remembered */
  }
  cache.clear();
}

function headers(): Record<string, string> {
  const t = getToken();
  return t ? { Accept: "application/json", Authorization: `Bearer ${t}` } : { Accept: "application/json" };
}

export async function getJson<T>(url: string): Promise<T> {
  if (cache.has(url)) return cache.get(url) as T;
  let res: Response;
  try {
    res = await fetch(url, { headers: headers() });
  } catch {
    throw new ApiError(url, 0, "The Workforce Intelligence API could not be reached.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(url, res.status, detail);
  }
  const data = (await res.json()) as T;
  cache.set(url, data);
  return data;
}

export interface ApiState<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
  retry: () => void;
}

export function useApi<T>(url: string | null): ApiState<T> {
  const [data, setData] = useState<T | undefined>(undefined);
  const [error, setError] = useState<ApiError | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(url !== null);
  const [nonce, setNonce] = useState(0);
  const current = useRef(url);

  useEffect(() => {
    current.current = url;
    if (url === null) {
      setLoading(false);
      return;
    }
    let alive = true;
    setLoading(true);
    setError(undefined);
    getJson<T>(url)
      .then((d) => {
        if (alive && current.current === url) setData(d);
      })
      .catch((e: unknown) => {
        if (alive && current.current === url)
          setError(e instanceof ApiError ? e : new ApiError(url, 0, String(e)));
      })
      .finally(() => {
        if (alive && current.current === url) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [url, nonce]);

  const retry = useCallback(() => {
    if (url) cache.delete(url);
    setNonce((n) => n + 1);
  }, [url]);

  return { data, error, loading, retry };
}

export const topic = (name: string) => `/api/topics/${name}`;
