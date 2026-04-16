"""Standalone config for the observability package (generated agent bundle).

Reads observability configuration from environment variables so the module
works without the main FastAPI application's core.config dependency.

Note: Azure AI Foundry evaluation settings are intentionally omitted — the
evaluation service is a centralised MAS platform service and does not run
inside the generated agent.
"""
import os


class _ObsSettings:  # noqa: D101
    # Agent / project identity — fixed at build time from spec/design metadata
    AGENT_NAME: str = 'Mathematical Operations Assistant'
    AGENT_ID: str = '8b11474a-1f71-49e6-bdaf-27ff58b2a4b8'
    PROJECT_NAME: str = 'Data Insights Project'
    PROJECT_ID: str = '1adaa46f-703c-467d-926b-014d70de76dd'

    # Observability database
    OBS_DATABASE_TYPE: str = os.getenv("OBS_DATABASE_TYPE", "sqlite")
    OBS_AZURE_SQL_SERVER: str = os.getenv("OBS_AZURE_SQL_SERVER", "")
    OBS_AZURE_SQL_DATABASE: str = os.getenv("OBS_AZURE_SQL_DATABASE", "")
    OBS_AZURE_SQL_SCHEMA: str = os.getenv("OBS_AZURE_SQL_SCHEMA", "dbo")
    OBS_AZURE_SQL_USERNAME: str = os.getenv("OBS_AZURE_SQL_USERNAME", "")
    OBS_AZURE_SQL_PASSWORD: str = os.getenv("OBS_AZURE_SQL_PASSWORD", "")
    OBS_AZURE_SQL_DRIVER: str = os.getenv(
        "OBS_AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server"
    )

    # OpenTelemetry / service identity
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", 'Mathematical Operations Assistant')
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    # Azure auth (used by engine.py for managed-identity / connection-string)
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")


settings = _ObsSettings()
