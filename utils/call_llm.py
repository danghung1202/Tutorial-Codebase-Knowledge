from google import genai
import os
import logging
import json
from datetime import datetime
import time
import requests.exceptions
from typing import Literal, Optional

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"

# Models configuration
MODEL_CONFIGS = {
    "gemini": {
        "default_model": "gemini-2.0-flash",
        "env_api_key": "GEMINI_API_KEY",
        "env_project_id": "GEMINI_PROJECT_ID", 
        "env_location": "GEMINI_LOCATION"
    },
    "claude": {
        "default_model": "claude-3-7-sonnet-20250219",
        "env_api_key": "ANTHROPIC_API_KEY"
    },
    "openai": {
        "default_model": "o1",
        "env_api_key": "OPENAI_API_KEY"
    },
    "deepseek": {
        "default_model": "deepseek-chat",
        "env_api_key": "DEEPSEEK_API_KEY"
    }
}

def call_llm(
    prompt: str, 
    model_provider: Literal["gemini", "claude", "openai", "deepseek"] = "gemini", 
    specific_model: Optional[str] = None,
    use_cache: bool = True
) -> str:
    """
    Call an LLM with the given prompt.
    
    Args:
        prompt: The text prompt to send to the LLM
        model_provider: Which LLM provider to use ("gemini", "claude", "openai", "deepseek")
        specific_model: Optional specific model name to override the default
        use_cache: Whether to use caching
        
    Returns:
        The text response from the LLM
    """
    # Log the prompt and model
    logger.info(f"MODEL: {model_provider}")
    logger.info(f"PROMPT: {prompt}")
    
    # Create cache key based on model and prompt
    cache_key = f"{model_provider}:{specific_model or 'default'}:{prompt}"
    
    # Check cache if enabled
    if use_cache:
        # Load cache from disk
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                logger.warning(f"Failed to load cache, starting with empty cache")
        
        # Return from cache if exists
        if cache_key in cache:
            logger.info(f"RESPONSE (cached): {cache[cache_key]}")
            return cache[cache_key]
    
    # Get response based on selected model
    response_text = ""
    
    if model_provider == "gemini":
        response_text = _call_gemini(prompt, specific_model)
    elif model_provider == "claude":
        response_text = _call_claude(prompt, specific_model)
    elif model_provider == "openai":
        response_text = _call_openai(prompt, specific_model)
    elif model_provider == "deepseek":
        response_text = _call_deepseek(prompt, specific_model)
    else:
        raise ValueError(f"Unknown model provider: {model_provider}")
    
    # Log the response
    logger.info(f"RESPONSE: {response_text}")
    
    # Update cache if enabled
    if use_cache:
        # Load cache again to avoid overwrites
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                pass
        
        # Add to cache and save
        cache[cache_key] = response_text
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    return response_text

def _call_gemini(prompt: str, specific_model: Optional[str] = None) -> str:
    """Call Google Gemini API"""
    config = MODEL_CONFIGS["gemini"]
    
    # Determine if using Vertex AI or API key
    use_vertex = os.getenv(config["env_project_id"], None) is not None
    
    if use_vertex:
        client = genai.Client(
            vertexai=True,
            project=os.getenv(config["env_project_id"], "your-project-id"),
            location=os.getenv(config["env_location"], "us-central1")
        )
    else:
        client = genai.Client(
            # Get API key from environment variable specified in config["env_api_key"]
            api_key=os.getenv(config["env_api_key"], "default_api_key is not set"),
        )
    
    # Use specific model if provided, otherwise use default or env var
    model_name = specific_model or config["default_model"]
    response = client.models.generate_content(
        model=model_name,
        contents=[prompt]
    )
    
    return response.text

def _call_claude(prompt: str, specific_model: Optional[str] = None) -> str:
    """Call Anthropic Claude API"""
    from anthropic import Anthropic
    
    config = MODEL_CONFIGS["claude"]
    api_key = os.environ.get(config["env_api_key"], "default_api_key is not set")
    model_name = specific_model or config["default_model"]
    
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_name,
        max_tokens=21000,
        thinking={
            "type": "enabled",
            "budget_tokens": 20000
        },
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[1].text

def _call_openai(prompt: str, specific_model: Optional[str] = None) -> str:
    """Call OpenAI API"""
    from openai import OpenAI
    
    config = MODEL_CONFIGS["openai"]
    api_key = os.environ.get(config["env_api_key"], "default_api_key is not set")
    model_name = specific_model or config["default_model"]
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "text"
        },
        reasoning_effort="medium",
        store=False
    )
    
    return response.choices[0].message.content

def _call_deepseek(prompt: str, specific_model: Optional[str] = None) -> str:
    """Call DeepSeek API"""
    from deepseek import DeepSeekAPI
    
    config = MODEL_CONFIGS["deepseek"]
    api_key = os.environ.get(config["env_api_key"], "default_api_key is not set")
    model_name = specific_model or config["default_model"]
    
    client = DeepSeekAPI(api_key=api_key)
    response = client.chat_completion(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
    return response.choices[0].message.content

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"
    
    # Test with different models
    print("Testing Gemini (default)...")
    response1 = call_llm(test_prompt, model_provider="gemini", use_cache=False)
    print(f"Gemini response: {response1[:100]}...")
    
    print("\nTesting with different provider (if available)...")
    try:
        response2 = call_llm(test_prompt, model_provider="openai", use_cache=False)
        print(f"OpenAI response: {response2[:100]}...")
    except Exception as e:
        print(f"OpenAI test failed: {e}")
    
