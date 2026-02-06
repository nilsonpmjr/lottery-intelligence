const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  db_exists: boolean;
  db_tables: string[];
}

export interface LotteryConfig {
  name: string;
  preco: number;
  total_nums: number;
  escolhe: number;
  orcamento_alvo: number;
}

export interface LotteriesResponse {
  lotteries: LotteryConfig[];
}

export interface GenerationJobRequest {
  loteria: string;
  orcamento: number;
  run_backtest?: boolean;
  backtest_last_n?: number;
}

export interface GameResult {
  numbers: number[];
  source: string;
  tag: string;
}

export interface GenerationStats {
  total_games: number;
  v3_count: number;
  v5_count: number;
}

export interface PerGameStat {
  game_index: number;
  avg_hits: number;
  max_hits: number;
  min_hits: number;
}

export interface BacktestResult {
  global_avg: number;
  global_max: number;
  per_game_stats: PerGameStat[];
  tested_draws: number;
}

export interface GenerationJobResponse {
  job_id: string;
  loteria: string;
  orcamento: number;
  games: GameResult[];
  stats: GenerationStats;
  backtest: BacktestResult | null;
  error: string | null;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchLotteries(): Promise<LotteriesResponse> {
  const res = await fetch(`${BASE_URL}/api/lotteries`);
  if (!res.ok) throw new Error(`Failed to fetch lotteries: ${res.status}`);
  return res.json();
}

export async function createGenerationJob(
  req: GenerationJobRequest
): Promise<GenerationJobResponse> {
  const res = await fetch(`${BASE_URL}/api/generation-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Generation failed (${res.status}): ${detail}`);
  }
  return res.json();
}
