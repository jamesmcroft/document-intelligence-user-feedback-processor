from app.common.dependencies.dependency_container import DependencyContainer

from app.common.app_settings import app_settings
from azure.identity import DefaultAzureCredential
from app.common.storage.storage_client_factory import StorageClientFactory
from app.features.models.services.model_documents_client import ModelDocumentsClient

if app_settings.azure_client_id:
    credential = DefaultAzureCredential(
        managed_identity_client_id=app_settings.azure_client_id,
        exclude_environment_credential=True,
        exclude_interactive_browser_credential=True,
        exclude_visual_studio_code_credential=True,
        exclude_shared_token_cache_credential=True,
        exclude_developer_cli_credential=True,
        exclude_powershell_credential=True,
        exclude_workload_identity_credential=True,
        process_timeout=10
    )
else:
    credential = DefaultAzureCredential(
        exclude_environment_credential=True,
        exclude_interactive_browser_credential=True,
        exclude_visual_studio_code_credential=True,
        exclude_shared_token_cache_credential=True,
        exclude_developer_cli_credential=True,
        exclude_powershell_credential=True,
        exclude_workload_identity_credential=True,
        process_timeout=10
    )


def _storage_client_factory(credential: DefaultAzureCredential) -> StorageClientFactory:
    return StorageClientFactory(credential)


def _model_documents_client(storage_client_factory: StorageClientFactory) -> ModelDocumentsClient:
    return ModelDocumentsClient(storage_client_factory)


dependencies = DependencyContainer()
dependencies.register_singleton(DefaultAzureCredential, credential)
dependencies.register_provider(StorageClientFactory, _storage_client_factory)
dependencies.register_provider(ModelDocumentsClient, _model_documents_client)
