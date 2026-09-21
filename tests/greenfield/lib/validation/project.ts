import { z } from "zod";

export const projectQuery = z.object({
  ownerId: z.coerce.number().int().positive(),
});
