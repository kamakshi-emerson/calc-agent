
# config.py

import os
import logging

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Configuration management for Mathematical Operations Assistant agent.
    Handles environment variables, API keys, LLM settings, domain-specific options,
    validation, error handling, and default values.
    """

    # Load environment variables using os.getenv()
    OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    # Domain-specific settings
    DOMAIN = "general"
    SYSTEM_PROMPT = (
        "You are a Mathematical Operations Assistant. "
        "You can help users perform a wide range of mathematical operations, "
        "including arithmetic, algebra, calculus, statistics, and more. "
        "When a user asks a question, provide a clear, step-by-step solution. "
        "If the question is ambiguous, ask clarifying questions. "
        "If the question cannot be answered, politely explain why."
    )
    OUTPUT_FORMAT = (
        "Return your answer as a clear, step-by-step explanation in markdown. "
        "If the question is ambiguous, ask for clarification. "
        "If you cannot answer, say 'I'm sorry, I cannot answer this question.'"
    )
    FALLBACK_RESPONSE = "I'm sorry, I cannot answer this question."

    @classmethod
    def validate(cls):
        """
        Validate required configuration values and handle errors.
        """
        errors = []
        if not cls.OPENAI_API_KEY:
            errors.append("Missing AZURE_OPENAI_API_KEY environment variable.")
        if not cls.OPENAI_ENDPOINT:
            errors.append("Missing AZURE_OPENAI_ENDPOINT environment variable.")
        if errors:
            for err in errors:
                logging.error(err)
            raise ConfigError("Configuration validation failed: " + "; ".join(errors))

    @classmethod
    def get_llm_config(cls):
        """
        Return LLM configuration as a dictionary.
        """
        return {
            "api_key": cls.OPENAI_API_KEY,
            "endpoint": cls.OPENAI_ENDPOINT,
            "model": cls.OPENAI_MODEL,
            "api_version": cls.OPENAI_API_VERSION
        }

    @classmethod
    def get_domain_settings(cls):
        """
        Return domain-specific settings.
        """
        return {
            "domain": cls.DOMAIN,
            "system_prompt": cls.SYSTEM_PROMPT,
            "output_format": cls.OUTPUT_FORMAT,
            "fallback_response": cls.FALLBACK_RESPONSE
        }

# Validate configuration at import time
try:
    Config.validate()
except ConfigError as e:
    # Proper error handling for missing API keys or other config errors
    logging.error(f"Agent configuration error: {e}")
    raise

# Example usage:
# llm_config = Config.get_llm_config()
# domain_settings = Config.get_domain_settings()
