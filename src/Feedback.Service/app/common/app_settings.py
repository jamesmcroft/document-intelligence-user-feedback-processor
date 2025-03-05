from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class AppSettings(BaseSettings):
    app_name: str = Field("Feedback.Service", env="APP_NAME")
    app_desc: str = Field("Feedback Service API", env="APP_DESC")
    environment: str = Field("dev", env="ENVIRONMENT")

    azure_client_id: Optional[str] = Field(..., env="AZURE_CLIENT_ID")
    azure_tenant_id: Optional[str] = Field(..., env="AZURE_TENANT_ID")
    azure_client_secret: Optional[str] = Field(..., env="AZURE_CLIENT_SECRET")

    applicationinsights_connection_string: Optional[str] = Field(..., env="APPLICATIONINSIGHTS_CONNECTION_STRING")
    otel_exporter_otlp_endpoint: Optional[str] = Field(..., env="OTEL_EXPORTER_OTLP_ENDPOINT")
    otel_exporter_export_interval: Optional[int] = Field(5000, env="OTEL_EXPORTER_EXPORT_INTERVAL")

    storage_account_name: str = Field(..., env="STORAGE_ACCOUNT_NAME")
    ai_services_endpoint: str = Field(..., env="AI_SERVICES_ENDPOINT")

    log_level: str = Field("INFO", env="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


app_settings = AppSettings()
