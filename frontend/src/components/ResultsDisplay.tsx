"use client";

import type { GenerationJobResponse } from "@/lib/api";

const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

function tagColor(tag: string): string {
  if (tag.toLowerCase().includes("v3"))
    return "bg-amber-600/20 text-amber-400 border-amber-600/30";
  if (tag.toLowerCase().includes("v5"))
    return "bg-green-600/20 text-green-400 border-green-600/30";
  return "bg-zinc-600/20 text-zinc-400 border-zinc-600/30";
}

interface ResultsDisplayProps {
  result: GenerationJobResponse | null;
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  if (!result) return null;

  const { stats, games, backtest } = result;

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="Total Games" value={stats.total_games} />
        <StatCard
          label="V3 Games"
          value={stats.v3_count}
          className="text-amber-400"
        />
        <StatCard
          label="V5 Games"
          value={stats.v5_count}
          className="text-green-400"
        />
      </div>

      {/* Games table */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50">
        <div className="border-b border-zinc-700 px-4 py-3">
          <h3 className="font-medium text-zinc-200">Generated Games</h3>
        </div>
        <div className="max-h-[28rem] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-zinc-800 text-left text-zinc-400">
              <tr>
                <th className="px-4 py-2 w-12">#</th>
                <th className="px-4 py-2 w-24">Tag</th>
                <th className="px-4 py-2">Numbers</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-700/50">
              {games.map((game, idx) => (
                <tr key={idx} className="text-zinc-300">
                  <td className="px-4 py-2 text-zinc-500">{idx + 1}</td>
                  <td className="px-4 py-2">
                    <span
                      className={`inline-block rounded border px-2 py-0.5 text-xs font-medium ${tagColor(game.tag)}`}
                    >
                      {game.tag}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex flex-wrap gap-1.5">
                      {game.numbers.map((n) => (
                        <span
                          key={n}
                          className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-zinc-700 text-xs font-medium text-zinc-200"
                        >
                          {String(n).padStart(2, "0")}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Backtest card */}
      {backtest && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50">
          <div className="border-b border-zinc-700 px-4 py-3">
            <h3 className="font-medium text-zinc-200">Backtest Results</h3>
          </div>
          <div className="p-4 space-y-4">
            {/* Headline numbers */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-zinc-100">
                  {backtest.global_avg.toFixed(2)}
                </p>
                <p className="text-xs text-zinc-500">Avg Hits</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-zinc-100">
                  {backtest.global_max}
                </p>
                <p className="text-xs text-zinc-500">Max Hits</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-zinc-100">
                  {backtest.tested_draws}
                </p>
                <p className="text-xs text-zinc-500">Draws Tested</p>
              </div>
            </div>

            {/* Per-game stats */}
            {backtest.per_game_stats.length > 0 && (
              <div className="max-h-48 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-zinc-800 text-left text-zinc-400">
                    <tr>
                      <th className="px-3 py-1.5">Game</th>
                      <th className="px-3 py-1.5">Avg</th>
                      <th className="px-3 py-1.5">Max</th>
                      <th className="px-3 py-1.5">Min</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-700/50 text-zinc-300">
                    {backtest.per_game_stats.map((pg) => (
                      <tr key={pg.game_index}>
                        <td className="px-3 py-1.5 text-zinc-500">
                          #{pg.game_index + 1}
                        </td>
                        <td className="px-3 py-1.5">
                          {pg.avg_hits.toFixed(2)}
                        </td>
                        <td className="px-3 py-1.5">{pg.max_hits}</td>
                        <td className="px-3 py-1.5">{pg.min_hits}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  className = "text-zinc-100",
}: {
  label: string;
  value: number;
  className?: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4 text-center">
      <p className={`text-2xl font-bold ${className}`}>{value}</p>
      <p className="text-xs text-zinc-500">{label}</p>
    </div>
  );
}
