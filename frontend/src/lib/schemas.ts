import { z } from "zod";

export const generationFormSchema = z.object({
  loteria: z.string().min(1, "Select a lottery"),
  orcamento: z.coerce
    .number({ message: "Budget must be a number" })
    .gt(0, "Budget must be greater than 0")
    .lte(1000, "Budget must be at most R$1.000"),
  run_backtest: z.boolean().default(true),
});

export type GenerationFormValues = z.infer<typeof generationFormSchema>;
export type GenerationFormInput = z.input<typeof generationFormSchema>;
