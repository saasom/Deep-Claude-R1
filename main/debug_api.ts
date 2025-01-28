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
        const requestBody = {
            model: "deepseek/deepseek-r1",
            messages: [
                {
                    role: "user",
                    content: process.argv[2] || "What is the capital of Norway?"
                }
            ],
            include_reasoning: true,
            temperature: 0
        };

        console.log('\n=== REQUEST TO DEEPSEEK ===');
        console.log(JSON.stringify(requestBody, null, 2));

        const response = await openai.chat.completions.create(requestBody as any);
        
        console.log('\n=== RAW DEEPSEEK RESPONSE ===');
        console.log(JSON.stringify(response, null, 2));

        // Extract the message for easier viewing
        const message = response.choices[0].message;
        console.log('\n=== DEEPSEEK MESSAGE ONLY ===');
        console.log(JSON.stringify(message, null, 2));

    } catch (error: any) {
        console.error('Error:', error);
        if (error.response) {
            console.error('Response data:', error.response.data);
            console.error('Response status:', error.response.status);
        }
        process.exit(1);
    }
}

// Only run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    testDeepSeek();
} 