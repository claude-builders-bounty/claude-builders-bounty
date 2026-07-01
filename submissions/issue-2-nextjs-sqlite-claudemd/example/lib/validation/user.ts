import { z } from "zod";

// One schema validates the request AND provides the TypeScript type.
export const createUserInput = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100).optional(),
});
export type CreateUserInput = z.infer<typeof createUserInput>;
