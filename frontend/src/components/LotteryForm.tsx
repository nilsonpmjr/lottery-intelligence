"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  generationFormSchema,
  type GenerationFormValues,
  type GenerationFormInput,
} from "@/lib/schemas";
import type { LotteryConfig } from "@/lib/api";

interface LotteryFormProps {
  lotteries: LotteryConfig[];
  onSubmit: (values: GenerationFormValues) => void;
  isLoading: boolean;
}

export default function LotteryForm({
  lotteries,
  onSubmit,
  isLoading,
}: LotteryFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<GenerationFormInput, unknown, GenerationFormValues>({
    resolver: zodResolver(generationFormSchema),
    defaultValues: {
      loteria: "",
      orcamento: undefined,
      run_backtest: true,
    },
  });

  const selectedLottery = lotteries.find((l) => l.name === watch("loteria"));
  const budget = Number(watch("orcamento")) || 0;
  const estimatedGames =
    selectedLottery && budget > 0
      ? Math.floor(budget / selectedLottery.preco)
      : null;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {/* Loteria */}
      <div>
        <label
          htmlFor="loteria"
          className="mb-1 block text-sm font-medium text-zinc-300"
        >
          Loteria
        </label>
        <select
          id="loteria"
          {...register("loteria")}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Selecione uma loteria...</option>
          {lotteries.map((l) => (
            <option key={l.name} value={l.name}>
              {l.name} (R${l.preco.toFixed(2)} &mdash; {l.escolhe} de{" "}
              {l.total_nums})
            </option>
          ))}
        </select>
        {errors.loteria && (
          <p className="mt-1 text-sm text-red-400">{errors.loteria.message}</p>
        )}
      </div>

      {/* Orcamento */}
      <div>
        <label
          htmlFor="orcamento"
          className="mb-1 block text-sm font-medium text-zinc-300"
        >
          Orcamento (R$)
        </label>
        <input
          id="orcamento"
          type="number"
          step="0.01"
          placeholder={
            selectedLottery
              ? String(selectedLottery.orcamento_alvo)
              : "Informe o valor"
          }
          {...register("orcamento")}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-zinc-100 placeholder-zinc-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.orcamento && (
          <p className="mt-1 text-sm text-red-400">
            {errors.orcamento.message}
          </p>
        )}
        {estimatedGames !== null && (
          <p className="mt-1 text-sm text-zinc-500">~{estimatedGames} jogos</p>
        )}
      </div>

      {/* Backtest */}
      <div className="flex items-center gap-2">
        <input
          id="run_backtest"
          type="checkbox"
          {...register("run_backtest")}
          className="h-4 w-4 rounded border-zinc-600 bg-zinc-800 text-blue-500 focus:ring-blue-500"
        />
        <label htmlFor="run_backtest" className="text-sm text-zinc-300">
          Executar analise de backtest
        </label>
      </div>

      {/* Enviar */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? "Gerando..." : "Gerar Jogos"}
      </button>
    </form>
  );
}
