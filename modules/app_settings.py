class AppSettings:
    def __init__(self, config: dict):
        self.managed_identity_client_id = config['AZURE_MANAGED_IDENTITY_CLIENT_ID']
        self.document_intelligence_endpoint = config['AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT']
        self.document_intelligence_key = config['AZURE_DOCUMENT_INTELLIGENCE_KEY']
        self.storage_account_name = config['AZURE_STORAGE_ACCOUNT_NAME']
        self.storage_account_connection_string = config['AZURE_STORAGE_ACCOUNT_CONNECTION_STRING']
        self.training_data_container_name = config['AZURE_DOCUMENT_INTELLIGENCE_TRAINING_DATA_CONTAINER_NAME']
