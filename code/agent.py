try:
    from observability.observability_wrapper import (
        trace_agent, trace_step, trace_step_sync, trace_model_call, trace_tool_call,
    )
    from observability.config import settings as _obs_settings
except ImportError:  # observability module not available (e.g. isolated test env)
    from contextlib import contextmanager as _obs_cm, asynccontextmanager as _obs_acm
    def trace_agent(*_a, **_kw):  # type: ignore[misc]
        def _deco(fn): return fn
        return _deco
    class _ObsHandle:
        output_summary = None
        def capture(self, *a, **kw): pass
    @_obs_acm
    async def trace_step(*_a, **_kw):  # type: ignore[misc]
        yield _ObsHandle()
    @_obs_cm
    def trace_step_sync(*_a, **_kw):  # type: ignore[misc]
        yield _ObsHandle()
    def trace_model_call(*_a, **_kw): pass  # type: ignore[misc]
    def trace_tool_call(*_a, **_kw): pass  # type: ignore[misc]
    class _ObsSettingsStub:
        AGENT_NAME: str = 'Mathematical Operations Assistant'
        PROJECT_NAME: str = 'Data Insights Project'
    _obs_settings = _ObsSettingsStub()

from modules.guardrails.content_safety_decorator import with_content_safety

GUARDRAILS_CONFIG = {'check_credentials_output': True,
 'check_jailbreak': True,
 'check_output': True,
 'check_pii_input': False,
 'check_toxic_code_output': True,
 'check_toxicity': True,
 'content_safety_enabled': True,
 'content_safety_severity_threshold': 3,
 'runtime_enabled': True,
 'sanitize_pii': False}


import os
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ValidationError
from dotenv import load_dotenv

# Observability wrappers are injected by the runtime; do not import manually.
# from observability import trace_step, trace_step_sync

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("math_ops_agent")

# =========================
# CONSTANTS
# =========================

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
FALLBACK_RESPONSE = (
    "I'm sorry, I cannot answer this question."
)

# =========================
# CONFIGURATION
# =========================

class Config:
    """
    Configuration loader for environment variables.
    """
    @staticmethod
    def get_openai_api_key() -> str:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            logger.error("AZURE_OPENAI_API_KEY not configured in environment.")
            raise ValueError("AZURE_OPENAI_API_KEY not configured in environment.")
        return api_key

    @staticmethod
    def get_openai_endpoint() -> str:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            logger.error("AZURE_OPENAI_ENDPOINT not configured in environment.")
            raise ValueError("AZURE_OPENAI_ENDPOINT not configured in environment.")
        return endpoint

    @staticmethod
    def get_openai_model() -> str:
        return os.getenv("OPENAI_MODEL", "gpt-4o")

    @staticmethod
    def get_openai_api_version() -> str:
        return os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

# =========================
# INPUT/OUTPUT MODELS
# =========================

class MathQueryRequest(BaseModel):
    """
    Request model for mathematical operation queries.
    """
    query: str = Field(..., description="The mathematical question or operation to perform.")

    @field_validator("query")
    @classmethod
    @with_content_safety(config=GUARDRAILS_CONFIG)
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query must not be empty.")
        if len(v) > 50000:
            raise ValueError("Query is too long (max 50,000 characters).")
        return v.strip()

class MathQueryResponse(BaseModel):
    """
    Response model for mathematical operation answers.
    """
    success: bool = Field(..., description="Whether the operation was successful.")
    answer: Optional[str] = Field(None, description="The answer or explanation.")
    error_type: Optional[str] = Field(None, description="Type of error if any.")
    error_message: Optional[str] = Field(None, description="Error message if any.")
    tips: Optional[str] = Field(None, description="Helpful tips for fixing input errors.")

# =========================
# LLM SERVICE
# =========================

class LLMService:
    """
    Handles interaction with Azure OpenAI for mathematical queries.
    """
    def __init__(self):
        self._client = None
        self._model = Config.get_openai_model()
        self._api_version = Config.get_openai_api_version()

    def get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncAzureOpenAI(
                api_key=Config.get_openai_api_key(),
                api_version=self._api_version,
                azure_endpoint=Config.get_openai_endpoint(),
            )
        return self._client

    async def get_math_answer(self, user_query: str) -> str:
        """
        Calls the LLM with the system prompt, user query, and output format.
        Returns the LLM's answer.
        """
        # Observability: trace_step for LLM call
        async with trace_step(
            "generate_math_answer", step_type="llm_call",
            decision_summary="Call LLM to answer mathematical question",
            output_fn=lambda r: f"length={len(r) if r else 0}",
        ) as step:
            client = self.get_client()
            system_message = f"{SYSTEM_PROMPT}\n\nOutput Format: {OUTPUT_FORMAT}"
            try:
                response = await client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.2,
                    max_tokens=3000
                )
                content = response.choices[0].message.content if response.choices else None
                step.capture(content)
                # Observability: trace_model_call
                try:
                    trace_model_call(
                        provider="openai",
                        model_name=self._model,
                        prompt_tokens=response.usage.prompt_tokens if hasattr(response, "usage") else None,
                        completion_tokens=response.usage.completion_tokens if hasattr(response, "usage") else None,
                        latency_ms=None,
                        response_summary=content[:200] if content else ""
                    )
                except Exception:
                    pass
                return content
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                step.capture(None)
                return None

# =========================
# AGENT
# =========================

class MathOperationsAgent:
    """
    Main agent class for mathematical operations.
    """
    def __init__(self):
        self.llm_service = LLMService()

    @trace_agent(agent_name=_obs_settings.AGENT_NAME, project_name=_obs_settings.PROJECT_NAME)
    @with_content_safety(config=GUARDRAILS_CONFIG)
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processes the user query and returns the answer.
        """
        # Observability: trace_step for input parsing
        async with trace_step(
            "parse_input", step_type="parse",
            decision_summary="Validate and sanitize user input",
            output_fn=lambda r: f"query={r[:50]}..." if r else "empty"
        ) as step:
            sanitized_query = query.strip()
            step.capture(sanitized_query)

        # Observability: trace_step for LLM call
        async with trace_step(
            "llm_math_answer", step_type="llm_call",
            decision_summary="Get answer from LLM",
            output_fn=lambda r: f"length={len(r) if r else 0}"
        ) as step:
            answer = await self.llm_service.get_math_answer(sanitized_query)
            step.capture(answer)

        if answer and answer.strip() and answer.strip() != FALLBACK_RESPONSE:
            return {
                "success": True,
                "answer": answer.strip(),
                "error_type": None,
                "error_message": None,
                "tips": None
            }
        else:
            return {
                "success": False,
                "answer": None,
                "error_type": "no_answer",
                "error_message": FALLBACK_RESPONSE,
                "tips": "Try rephrasing your question or provide more details."
            }

# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="Mathematical Operations Assistant",
    description="An API for performing mathematical operations and answering math questions using LLM.",
    version="1.0.0"
)

agent = MathOperationsAgent()

@app.post("/query", response_model=MathQueryResponse)
@with_content_safety(config=GUARDRAILS_CONFIG)
async def query_math(req: MathQueryRequest):
    """
    Endpoint to process mathematical queries.
    """
    try:
        # Input validation is handled by Pydantic
        result = await agent.process_query(req.query)
        return MathQueryResponse(**result)
    except ValidationError as ve:
        logger.warning(f"Validation error: {ve}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "answer": None,
                "error_type": "validation_error",
                "error_message": "Invalid input.",
                "tips": str(ve)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "answer": None,
                "error_type": "internal_error",
                "error_message": "An unexpected error occurred.",
                "tips": "Please try again later."
            }
        )

# =========================
# ERROR HANDLERS
# =========================

@app.exception_handler(ValidationError)
@with_content_safety(config=GUARDRAILS_CONFIG)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Malformed JSON or validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "answer": None,
            "error_type": "validation_error",
            "error_message": "Malformed JSON or validation error.",
            "tips": "Check your JSON formatting, ensure all required fields are present and valid."
        }
    )

@app.exception_handler(Exception)
@with_content_safety(config=GUARDRAILS_CONFIG)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "answer": None,
            "error_type": "internal_error",
            "error_message": "An unexpected error occurred.",
            "tips": "Please check your request and try again."
        }
    )

# =========================
# MAIN ENTRY POINT
# =========================

if __name__ == "__main__":
    import asyncio
    import uvicorn

    @trace_agent(agent_name=_obs_settings.AGENT_NAME, project_name=_obs_settings.PROJECT_NAME)
    async def main():
        config = uvicorn.Config("agent:app", host="0.0.0.0", port=8080, reload=False)
        server = uvicorn.Server(config)
        await server.serve()

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Failed to start server: {e}")