import OpenAI from 'openai';
import { fileURLToPath } from 'url';
import axios, { isAxiosError } from 'axios';
import { DeepSeekResultSchema } from './validation.js';

// Define the extended types for DeepSeek's response format
type DeepSeekMessage = {
    role: 'assistant' | 'user';
    content: string;
    reasoning?: string | null;
}

type DeepSeekResult = {
    reasoning: string;
    answer: string;
}

async function main(): Promise<DeepSeekResult> {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
        console.error('OPENROUTER_API_KEY environment variable is required');
        process.exit(1);
    }

    const openai = new OpenAI({
        baseURL: "https://openrouter.ai/api/v1",
        apiKey: apiKey,
        defaultHeaders: {
            "HTTP-Referer": "https://github.com/yourusername/Deep-Claude-R1",
            "X-Title": "Deep-Claude-R1"
        }
    });

    try {
        const requestBody = {
            model: "deepseek/deepseek-r1",
            messages: [
                {
                    role: "user",
                    content: process.argv[2] || "What is the capital of France?"
                }
            ],
            include_reasoning: true,
            temperature: 0  // For consistent responses
        };
        
        console.log('Sending request:', JSON.stringify(requestBody, null, 2));
        
        const completion = await openai.chat.completions.create(requestBody as any);
        const message = completion.choices[0].message as DeepSeekMessage;

        let result: DeepSeekResult = {
            reasoning: '',
            answer: ''
        };

        // Update the content parsing section with more robust pattern matching
        const content = message.content || '';

        // Debug raw response
        console.log('Raw response content:', JSON.stringify(content));

        // New: Handle numbered list format
        const numberedListMatch = content.match(/(\d+\.\s*Reasoning:[\s\S]*?)(\d+\.\s*Answer:[\s\S]*)/i);
        if (numberedListMatch) {
            result.reasoning = numberedListMatch[1].replace(/^\d+\.\s*Reasoning:\s*/i, '').trim();
            result.answer = numberedListMatch[2].replace(/^\d+\.\s*Answer:\s*/i, '').trim();
        } 
        // New: Handle markdown bold headers
        else if (content.includes('**Reasoning**')) {
            const parts = content.split('**Answer**');
            result.reasoning = parts[0].replace('**Reasoning**', '').trim();
            result.answer = parts[1]?.trim() || '';
        }
        // Existing parsing logic with improved regex
        else {
            // Modified to handle different capitalization and spacing
            const standardizedContent = content
                .replace(/(Reasoning|Analysis|Thought Process):?/gi, 'REASONING:')
                .replace(/(Answer|Final Answer|Conclusion):?/gi, 'ANSWER:');

            // Add markdown code block extraction
            const extractFromCodeBlocks = (text: string) => {
                const codeBlockMatch = text.match(/```(?:json)?\n([\s\S]*?)\n```/);
                if (codeBlockMatch) {
                    try {
                        return JSON.parse(codeBlockMatch[1]);
                    } catch (e) {
                        console.log('Failed to parse code block, using text content');
                    }
                }
                return null;
            };

            // Try extracting from code blocks first
            const codeBlockContent = extractFromCodeBlocks(standardizedContent);
            if (codeBlockContent) {
                result.reasoning = codeBlockContent.reasoning || '';
                result.answer = codeBlockContent.answer || '';
            } else {
                // Existing parsing logic...
                result.reasoning = standardizedContent.split('ANSWER:')[0].replace('REASONING:', '').trim();
                result.answer = standardizedContent.split('ANSWER:')[1]?.trim() || '';

                // If that didn't work, try alternative splits
                if (!result.answer) {
                    const answerParts = standardizedContent.split(/(?:###|##) Answer/);
                    if (answerParts.length > 1) {
                        result.answer = answerParts[1].trim();
                        result.reasoning = answerParts[0].replace('REASONING:', '').trim();
                    }
                }

                // Final fallback to newline splitting
                if (!result.answer) {
                    const parts = content.split('\n').filter(p => p.trim());
                    if (parts.length > 0) {
                        [result.answer] = parts.slice(-1);
                        result.reasoning = parts.slice(0, -1).join('\n').trim();
                    }
                }
            }
        }

        // New: Final cleanup of empty answers
        if (result.answer === '' && content.trim().length > 0) {
            result.answer = content.trim().split('\n').pop()?.trim() || content.trim();
        }

        // Add final validation with error handling
        try {
            const parsedResult = DeepSeekResultSchema.parse(result);
        } catch (validationError) {
            console.error('Validation failed:', validationError);
            result.answer = content.trim(); // Fallback to raw content
            result.reasoning = 'Could not parse reasoning from response';
        }

        // Write result to stdout in a way that Python can parse
        console.log('\n=== DEEPSEEK RESULT ===');
        console.log(JSON.stringify(result));
        console.log('=== END DEEPSEEK RESULT ===');

        // Add this right after getting the completion
        console.log('Full API response:', JSON.stringify(completion, null, 2));

        return result;

    } catch (error: unknown) {
        console.error('Error:', error);
        if (isAxiosError(error)) {
            console.error('HTTP status:', error.response?.status);
            console.error('Response data:', error.response?.data);
        } else if (error instanceof Error) {
            console.error('Error message:', error.message);
        }
        process.exit(1);
    }
}

// Only run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
} 