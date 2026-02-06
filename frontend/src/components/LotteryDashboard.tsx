"use client";

import { useEffect, useState } from "react";
import {
  fetchLotteries,
  createGenerationJob,
  type LotteryConfig,
  type GenerationJobResponse,
} from "@/lib/api";
import type { GenerationFormValues } from "@/lib/schemas";
import HealthIndicator from "./HealthIndicator";
import LotteryForm from "./LotteryForm";
import ResultsDisplay from "./ResultsDisplay";

export default function LotteryDashboard() {
  const [lotteries, setLotteries] = useState<LotteryConfig[]>([]);
  const [result, setResult] = useState<GenerationJobResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLotteries()
      .then((res) => setLotteries(res.lotteries))
      .catch((err) => setError(err.message));
  }, []);

  async function handleSubmit(values: GenerationFormValues) {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await createGenerationJob({
        loteria: values.loteria,
        orcamento: values.orcamento,
        run_backtest: values.run_backtest,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">
            Lottery Intelligence
          </h1>
          <p className="text-sm text-zinc-500">
            AI-powered number generation and backtesting
          </p>
        </div>
        <HealthIndicator />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 flex items-center justify-between rounded-lg border border-red-600/30 bg-red-600/10 px-4 py-3 text-sm text-red-400">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-400 hover:text-red-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Form */}
      <div className="mb-8 rounded-lg border border-zinc-700 bg-zinc-800/50 p-6">
        <LotteryForm
          lotteries={lotteries}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="mb-8 flex items-center justify-center gap-3 py-12 text-zinc-400">
          <svg
            className="h-5 w-5 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          Generating games...
        </div>
      )}

      {/* Results */}
      <ResultsDisplay result={result} />
    </div>
  );
}
