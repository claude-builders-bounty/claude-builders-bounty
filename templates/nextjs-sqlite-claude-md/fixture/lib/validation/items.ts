import { z } from 'zod';

export const ItemInputSchema = z.object({
  title: z.string().min(1).max(200),
});

export type ItemInput = z.infer<typeof ItemInputSchema>;
