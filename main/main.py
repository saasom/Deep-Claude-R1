#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from termcolor import colored
from anthropic import Anthropic
from halo import Halo
import time
from fuzzywuzzy import fuzz
from typing import List, Dict, Tuple, Optional

# Read API keys from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Make the Claude prompt configurable
CLAUDE_PROMPT_TEMPLATE = """Analyze this problem-solving attempt:

Question: {question}
DeepSeek's Reasoning: {reasoning}

Provide:
1. Strengths of this approach
2. Potential improvements
3. Alternative perspectives
4. Final optimized answer

Format with clear section headers (##)"""

# Add configurable model parameters
class Config:
    def __init__(self):
        self.max_deepseek_tokens: int = 2000
        self.claude_temperature: float = 0.7
        self.enable_debug_logs: bool = False
        self.agreement_threshold: float = 0.7
        self.request_timeout: int = 30
        self.enable_haiku_comparison: bool = True
        self.comparison_model: str = "claude-3-haiku-20240307"
        self.comparison_temperature: float = 0.3
        self.max_comparison_tokens: int = 400

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        config = cls()
        config.enable_debug_logs = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        config.max_deepseek_tokens = int(os.getenv('MAX_TOKENS', '2000'))
        config.claude_temperature = float(os.getenv('TEMPERATURE', '0.7'))
        return config

# Load from environment variables
config = Config.from_env()

def print_header(text: str, color: str = "yellow", width: int = 80):
    """Print a centered header with fancy box drawing characters."""
    print("\n" + colored("╔" + "═" * (width-2) + "╗", color))
    padding = (width - len(text) - 2) // 2
    print(colored("║" + " " * padding + text + " " * (width - padding - len(text) - 2) + "║", color))
    print(colored("╚" + "═" * (width-2) + "╝", color) + "\n")

def print_section(title: str, content: str, color: str = "white"):
    """Print a section with fancy box drawing characters."""
    print(colored("╭─── " + title + " ", color) + colored("─" * (75 - len(title)), color))
    for line in content.split('\n'):
        print(colored("│ ", color) + line)
    print(colored("╰" + "─" * 78, color))

def format_code(text: str) -> str:
    """Format text as code with syntax highlighting."""
    return text

def call_openrouter_api(question: str) -> tuple[str, str, float]:
    """Call OpenRouter API using our TypeScript module."""
    start_time = time.time()
    try:
        spinner = Halo(text='Initializing TypeScript module...', spinner='dots', color='blue')
        spinner.start()
        
        # Check if the compiled JS file exists
        js_path = 'dist/openrouter.js'
        if not os.path.exists(js_path):
            spinner.fail('TypeScript module not found')
            raise Exception(f"Compiled JavaScript file not found at {js_path}. Did you run 'npm run build'?")
        
        spinner.succeed('TypeScript module initialized')
        
        # Run the TypeScript code through Node.js
        cmd = [
            'node',
            js_path,
            question
        ]
        
        # Set up environment variables
        env = os.environ.copy()
        env['OPENROUTER_API_KEY'] = OPENROUTER_API_KEY
        
        spinner.text = 'Calling DeepSeek via OpenRouter...'
        spinner.start()
        
        # Run the process and capture output
        process = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        
        if process.returncode != 0:
            spinner.fail('DeepSeek API call failed')
            raise Exception(f"TypeScript process failed with code {process.returncode}: {process.stderr}")

        # Find the JSON result between the markers
        output = process.stdout
        start_marker = "=== DEEPSEEK RESULT ==="
        end_marker = "=== END DEEPSEEK RESULT ==="
        
        start_idx = output.find(start_marker)
        end_idx = output.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            spinner.fail('Failed to parse DeepSeek response')
            raise Exception("Could not find result markers in output")
            
        json_str = output[start_idx + len(start_marker):end_idx].strip()
        result = json.loads(json_str)
        
        spinner.succeed('Received response from DeepSeek')
        end_time = time.time()
        return result['answer'], result['reasoning'], end_time - start_time
        
    except Exception as e:
        if 'spinner' in locals():
            spinner.fail('Error in DeepSeek API call')
        print(colored(f"Error details: {e}", "red"))
        return "[Error getting answer]", "[Error getting reasoning]", 0.0

def check_agreement(deepseek: str, claude: str, threshold: float = 0.7) -> bool:
    """Compare the similarity between two model responses.
    
    Args:
        deepseek: Response from DeepSeek model
        claude: Response from Claude model
        threshold: Minimum similarity ratio (0.0 to 1.0)
    
    Returns:
        bool: True if responses are sufficiently similar
    """
    simplified_deepseek = deepseek.lower().split('.')[0]
    simplified_claude = claude.lower().split('.')[0]
    return fuzz.ratio(simplified_deepseek, simplified_claude) / 100 > threshold

def print_conversation_history(history: List[Dict]) -> None:
    """Display formatted conversation history.
    
    Args:
        history: List of conversation entries containing questions and responses
    """
    print_header("Conversation History", "blue")
    for i, entry in enumerate(history, 1):
        print_section(f"Session {i}", 
            f"Question: {entry['question']}\n"
            f"DeepSeek Answer: {entry['deepseek']['answer']}\n"
            f"Claude Answer: {entry['claude']}", "yellow")

def compare_responses(question: str, deepseek: str, claude: str) -> str:
    """Use Claude Haiku to analyze and compare model responses."""
    comparison_prompt = f"""Analyze these two responses to the question "{question}":
    
    [DeepSeek Response]
    {deepseek}
    
    [Claude Response] 
    {claude}
    
    Compare them by:
    1. Identifying 3 key differences in approach
    2. Noting one strength of each
    3. Highlighting any factual discrepancies
    4. Judging which is more comprehensive
    5. Suggesting potential improvements
    
    Use bullet points and keep analysis under 5 sentences."""

    try:
        response = anthropic_client.messages.create(
            model=config.comparison_model,
            max_tokens=config.max_comparison_tokens,
            temperature=config.comparison_temperature,
            messages=[{
                "role": "user",
                "content": comparison_prompt
            }]
        )
        return response.content[0].text
    except Exception as e:
        return f"Comparison failed: {str(e)}"

def main():
    # Print welcome banner
    print_header("🤖 Deep-Claude Reasoning Chain 🤖", "cyan", width=80)
    print_section("Status", 
        f"OpenRouter API Key: {'✓' if OPENROUTER_API_KEY else '✗'}\n"
        f"Claude API Key: {'✓' if ANTHROPIC_API_KEY else '✗'}", 
        "blue")

    # Add to main()
    conversation_history = []

    # Start chat loop
    while True:
        try:
            # Get the question
            if len(sys.argv) > 1:
                question = " ".join(sys.argv[1:])
                sys.argv = [sys.argv[0]]  # Clear args for subsequent loops
            else:
                question = input(colored("\n🤔 Enter your question (or 'exit' to quit): ", "cyan"))
                if question.lower() in ['exit', 'quit']:
                    print(colored("\n👋 Goodbye!", "yellow"))
                    break
                elif question.lower() == 'history':
                    print_conversation_history(conversation_history)
                    continue

            print_header("Question", "yellow")
            print_section("Input", question, "cyan")

            # Get response from OpenRouter via TypeScript
            deepseek_answer, deepseek_reasoning, deepseek_time = call_openrouter_api(question)

            print_header("DeepSeek's Analysis 🔍", "green")
            print_section("Reasoning Process", deepseek_reasoning, "cyan")
            print_section("Initial Answer", deepseek_answer, "green")

            # Send reasoning + original question to Claude
            print_header("Claude's Analysis 🤔", "magenta")
            claude_request = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8000,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"'{question}' given this question, and the following reasoning:\n\n"
                            f"{deepseek_reasoning}\n\n"
                            f"What is your answer to '{question}'?"
                        )
                    }
                ]
            }

            print_section("Prompt", claude_request["messages"][0]["content"], "blue")
            
            spinner = Halo(text='Waiting for Claude...', spinner='dots', color='magenta')
            spinner.start()
            
            claude_start = time.time()
            claude_response = anthropic_client.messages.create(
                **claude_request,
                timeout=30
            )
            claude_time = time.time() - claude_start
            
            spinner.succeed('Received response from Claude')

            final_answer = claude_response.content[0].text
            print_section("Response", final_answer, "magenta")

            # Print comparison summary
            print_header("Final Comparison 🎯", "yellow")
            print_section("DeepSeek's Answer", deepseek_answer, "green")
            print_section("Claude's Answer", final_answer, "magenta")

            # In the chat loop after getting Claude's response:
            conversation_history.append({
                "question": question,
                "deepseek": {"answer": deepseek_answer, "reasoning": deepseek_reasoning},
                "claude": final_answer
            })

            # Then display timing info in the output
            print_section("Performance", 
                f"DeepSeek Response: {deepseek_time:.2f}s\n"
                f"Claude Response: {claude_time:.2f}s", "yellow")

            # Replace the existing agreement check with:
            print_header("Expert Analysis 🧐", "cyan")
            spinner = Halo(text='Asking Haiku to compare responses...', spinner='dots', color='cyan')
            spinner.start()
            analysis = compare_responses(question, deepseek_answer, final_answer)
            spinner.succeed()

            print_section("Haiku's Comparison", analysis, "cyan")

            # Keep the existing agreement check as fallback
            if not check_agreement(deepseek_answer, final_answer):
                print_section("⚠️ Warning", "Models show significant divergence!", "red")

        except Exception as e:
            if 'spinner' in locals():
                spinner.fail('Error occurred')
            print_section("Error", str(e), "red")
            continue

if __name__ == "__main__":
    main()