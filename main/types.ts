import OpenAI from 'openai';

export interface DeepSeekRequest {
  model: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  include_reasoning?: boolean;
  temperature?: number;
}

export interface DeepSeekResponse extends OpenAI.Chat.Completions.ChatCompletion {
  choices: Array<OpenAI.Chat.Completions.ChatCompletion.Choice & {
    message: {
      content: string;
      reasoning?: string;
    }
  }>;
}

export class ValidationError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'ValidationError';
    }
}

export class ParseError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'ParseError';
    }
} 