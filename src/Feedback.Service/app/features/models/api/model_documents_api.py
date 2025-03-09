from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from app.common.versioning.versioning import version, VersionedRoute, get_api_version, DEFAULT_API_VERSION
from app.features.models.services.model_documents_client import ModelDocumentsClient
from app.dependencies import dependencies as service_collection

router = APIRouter(prefix="/{model_id}",
                   route_class=VersionedRoute,
                   dependencies=[Depends(get_api_version)])


@router.get("/documents", status_code=status.HTTP_200_OK, operation_id="listModelDocuments")
@version(DEFAULT_API_VERSION)
async def list_documents(model_id: str):
    model_documents_client = service_collection.resolve(ModelDocumentsClient)
    return model_documents_client.list_model_documents("UseDevelopmentStorage=true", model_id)


@router.post("/documents", status_code=status.HTTP_201_CREATED, operation_id="uploadModelDocument")
@version(DEFAULT_API_VERSION)
async def upload_document(file: UploadFile = File(...)):
    return {"filename": file.filename}


@router.get("/documents/{document_id}", status_code=status.HTTP_200_OK, operation_id="getModelDocument")
@version(DEFAULT_API_VERSION)
async def get_document(document_id: int):
    return {"document_id": document_id}


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteModelDocument")
@version(DEFAULT_API_VERSION)
async def delete_document(document_id: int):
    return None
