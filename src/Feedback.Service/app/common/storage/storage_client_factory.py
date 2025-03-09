from typing import Optional
from azure.core.credentials import TokenCredential
from azure.storage.blob import BlobServiceClient


class StorageClientFactory:
    STORAGE_EMULATOR_CONNECTION_STRING = (
        "DefaultEndpointsProtocol=http",
        "AccountName=devstoreaccount1",
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==",
        "BlobEndpoint=http://localhost:10000/devstoreaccount1",
        "QueueEndpoint=http://localhost:10001/devstoreaccount1",
        "TableEndpoint=http://localhost:10002/devstoreaccount1",
    )

    def __init__(self, credential: TokenCredential):
        self._credential = credential

    def get_blob_service_client(self, storage_account_name: str) -> BlobServiceClient:
        if self._is_development_storage_account(storage_account_name):
            return BlobServiceClient.from_connection_string(
                ";".join(self.STORAGE_EMULATOR_CONNECTION_STRING)
            )

        return BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=self._credential
        )

    def _is_development_storage_account(self, storage_account_name: Optional[str]) -> bool:
        if storage_account_name is None:
            return False

        return storage_account_name == "devstoreaccount1" or storage_account_name.startswith("UseDevelopmentStorage")
