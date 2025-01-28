import { z } from 'zod';

export const DeepSeekResultSchema = z.object({
  reasoning: z.string(),
  answer: z.string()
}); 