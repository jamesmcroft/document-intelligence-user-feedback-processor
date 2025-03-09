from azure.core.credentials import TokenCredential, AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from app.common.storage.storage_client_factory import StorageClientFactory

class ModelDocumentsClient:
    """A client for managing documents associated with Document Intelligence models."""

    def __init__(self, storage_client_factory: StorageClientFactory):
        """Initializes the ModelDocumentsClient.

        :param storage_client_factory: The factory for creating storage clients.
        """

        self._storage_client_factory = storage_client_factory

    def list_model_documents(self, storage_account_name: str, model_id: str):
        """Lists the documents associated with a model (excluding any JSON metadata files).

        :param model_id: The ID of the model (container) to list documents for.
        """

        blob_service_client = self._storage_client_factory.get_blob_service_client(storage_account_name)
        container_client = blob_service_client.get_container_client(model_id)
        blob_list = container_client.list_blobs()
        documents = [blob.name for blob in blob_list if not blob.name.endswith(".json")]

        return {"documents": documents}
