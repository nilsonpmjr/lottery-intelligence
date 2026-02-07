import { z } from "zod";

export const generationFormSchema = z.object({
  loteria: z.string().min(1, "Selecione uma loteria"),
  orcamento: z.coerce
    .number({ message: "O valor deve ser um numero" })
    .gt(0, "O valor deve ser maior que zero")
    .lte(1000, "O valor deve ser no maximo R$1.000"),
  run_backtest: z.boolean().default(true),
});

export type GenerationFormValues = z.infer<typeof generationFormSchema>;
export type GenerationFormInput = z.input<typeof generationFormSchema>;
