import { z } from 'zod';

// Constants for validation
const MIN_REASONING_LENGTH = 100;
const MIN_ANSWER_LENGTH = 2;

// Export the schema type
export type DeepSeekResult = z.infer<typeof DeepSeekResultSchema>;

export const DeepSeekResultSchema = z.object({
  reasoning: z.string().min(
    MIN_REASONING_LENGTH,
    `Reasoning too short (min ${MIN_REASONING_LENGTH} chars) - possible parsing error`
  ),
  answer: z.string().min(
    MIN_ANSWER_LENGTH,
    `Answer too short (min ${MIN_ANSWER_LENGTH} chars) - possible parsing error`
  )
}).refine(
  data => !data.answer.includes("Error getting"),
  { message: "API call failed - check network connection" }
); 