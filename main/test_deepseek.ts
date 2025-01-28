import OpenAI from 'openai';
import { fileURLToPath } from 'url';

async function testDeepSeek() {
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
        // Test with a simple question
        const requestBody = {
            model: "deepseek/deepseek-r1",
            messages: [
                {
                    role: "user",
                    content: "What is 2+2? Please show your reasoning step by step."
                }
            ],
            include_reasoning: true,
            temperature: 0 // Set to 0 for consistent responses
        };

        console.log('\n=== REQUEST DETAILS ===');
        console.log(JSON.stringify(requestBody, null, 2));

        const response = await openai.chat.completions.create(requestBody as any);

        // Log the complete OpenRouter response object
        console.log('\n=== COMPLETE RESPONSE OBJECT ===');
        console.log(JSON.stringify(response, null, 2));

        // Extract and log specific parts
        const message = response.choices[0].message;
        console.log('\n=== MESSAGE OBJECT ===');
        console.log('Message keys:', Object.keys(message));
        console.log('Full message:', JSON.stringify(message, null, 2));

        // Log any additional response properties
        console.log('\n=== ADDITIONAL PROPERTIES ===');
        console.log('Response keys:', Object.keys(response));
        
        // Log model info if available
        if ('model' in response) {
            console.log('\n=== MODEL INFO ===');
            console.log('Model:', response.model);
        }

        // Log any metadata/headers
        if ('headers' in response) {
            console.log('\n=== RESPONSE HEADERS ===');
            console.log(response.headers);
        }

    } catch (error: any) {
        console.error('\n=== ERROR ===');
        console.error('Error type:', error.constructor.name);
        console.error('Error message:', error.message);
        if (error.response) {
            console.error('\nResponse error data:', error.response.data);
            console.error('Response status:', error.response.status);
        }
        console.error('\nFull error:', error);
    }
}

// Only run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    testDeepSeek();
} 