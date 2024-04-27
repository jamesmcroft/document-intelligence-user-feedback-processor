import os
from azure.ai.formrecognizer import (DocumentModelAdministrationClient,
                                     ModelBuildMode,
                                     DocumentAnalysisClient)
from azure.core.credentials import (TokenCredential, AzureKeyCredential)
from azure.storage.blob import (BlobServiceClient)
from modules.document_intelligence_result_formatter import DocumentIntelligenceResultFormatter
from modules.app_settings import AppSettings


class ModelTrainingClient:
    """A client for training Document Intelligence models and running layout analysis on documents."""

    def __init__(self, settings: AppSettings, use_azure_credential: bool = False, azure_credential: TokenCredential | None = None):
        """Initializes the ModelTrainingClient.

        :param config: The configuration settings for the client.
        :param azure_credential: The Azure credential to use for authentication.
        """

        document_intelligence_endpoint = settings.document_intelligence_endpoint
        document_intelligence_key = settings.document_intelligence_key
        storage_account_name = settings.storage_account_name
        storage_account_connection_string = settings.storage_account_connection_string
        training_data_container_name = settings.training_data_container_name

        if use_azure_credential:
            blob_service_client = BlobServiceClient(
                account_url=f"https://{storage_account_name}.blob.core.windows.net", credential=azure_credential)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(
                storage_account_connection_string
            )
            azure_credential = AzureKeyCredential(document_intelligence_key)

        self.training_data_container_client = blob_service_client.get_container_client(
            training_data_container_name)
        self.document_model_admin_client = DocumentModelAdministrationClient(
            endpoint=document_intelligence_endpoint, credential=azure_credential)
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=document_intelligence_endpoint, credential=azure_credential)

    def upload_training_data(self, training_data_folder_path: str):
        """Uploads the training data to the Azure Blob Storage container.

        :param training_data_folder_path: The path to the folder containing the training data.
        """

        for root, _, files in os.walk(training_data_folder_path):
            for file in files:
                blob_client = self.training_data_container_client.get_blob_client(
                    file)
                with open(f"{root}/{file}", "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)

        self.training_data_container_client_sas_url = f"{
            self.training_data_container_client.url}"

    def delete_training_data(self, blob_name_search: str):
        """Deletes the training data from the Azure Blob Storage container.

        :param blob_name_search: The search string to use to find the blobs to delete.
        """

        blob_list = self.training_data_container_client.list_blobs()
        for blob in blob_list:
            if blob_name_search in blob.name:
                blob_client = self.training_data_container_client.get_blob_client(
                    blob.name)
                blob_client.delete_blob()

    def create_model(self, model_name: str):
        """Creates a Document Intelligence model.

        :param model_name: The name of the model to create.
        :return: The created model details.
        """

        try:
            self.document_model_admin_client.delete_document_model(model_name)
        except:
            pass

        poller = self.document_model_admin_client.begin_build_document_model(
            build_mode=ModelBuildMode.TEMPLATE,
            blob_container_url=self.training_data_container_client_sas_url,
            model_id=model_name
        )
        self.model = poller.result()
        return self.model

    def run_layout_analysis(self, file_path: str, output_ocr_json_path: str, model_name='prebuilt-layout'):
        """Runs layout analysis on a document.

        :param file_path: The path to the document to analyze.
        :param output_ocr_json_path: The path to save the OCR JSON output.
        :param model_name: The name of the model to use for analysis.
        :return: The OCR JSON output.
        """

        with open(file_path, "rb") as f:
            poller = self.document_analysis_client.begin_analyze_document(
                model_id=model_name, document=f)
            self.analysis_result = poller.result()
        return DocumentIntelligenceResultFormatter.save_to_ocr_json(self.analysis_result, output_ocr_json_path)
