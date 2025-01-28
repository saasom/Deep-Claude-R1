#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from termcolor import colored
from anthropic import Anthropic
from halo import Halo

# Read API keys from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

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

def call_openrouter_api(question: str) -> tuple[str, str]:
    """Call OpenRouter API using our TypeScript module."""
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
        return result['answer'], result['reasoning']
        
    except Exception as e:
        if 'spinner' in locals():
            spinner.fail('Error in DeepSeek API call')
        print(colored(f"Error details: {e}", "red"))
        return "[Error getting answer]", "[Error getting reasoning]"

def main():
    # Print welcome banner
    print_header("🤖 Deep-Claude Reasoning Chain 🤖", "cyan", width=80)
    print_section("Status", 
        f"OpenRouter API Key: {'✓' if OPENROUTER_API_KEY else '✗'}\n"
        f"Claude API Key: {'✓' if ANTHROPIC_API_KEY else '✗'}", 
        "blue")

    # Get the question
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input(colored("🤔 Enter your question: ", "cyan"))

    print_header("Question", "yellow")
    print_section("Input", question, "cyan")

    try:
        # Get response from OpenRouter via TypeScript
        deepseek_answer, deepseek_reasoning = call_openrouter_api(question)

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
        
        claude_response = anthropic_client.messages.create(
            **claude_request,
            timeout=30
        )
        
        spinner.succeed('Received response from Claude')

        final_answer = claude_response.content[0].text
        print_section("Response", final_answer, "magenta")

        # Print comparison summary
        print_header("Final Comparison 🎯", "yellow")
        print_section("DeepSeek's Answer", deepseek_answer, "green")
        print_section("Claude's Answer", final_answer, "magenta")

    except Exception as e:
        if 'spinner' in locals():
            spinner.fail('Error occurred')
        print_section("Error", str(e), "red")

if __name__ == "__main__":
    main()