from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends
from app.common.versioning.versioning import version, VersionedRoute, get_api_version

router = APIRouter(route_class=VersionedRoute, dependencies=[Depends(get_api_version)])

@router.get("/documents", status_code=status.HTTP_200_OK)
@version("2025-01-01")
async def list_documents():
    return {"documents": []}

@router.post("/documents", status_code=status.HTTP_201_CREATED)
@version("2025-04-01-preview")
async def upload_document(file: UploadFile = File(...)):
    return {"filename": file.filename}

@router.get("/documents/{document_id}", status_code=status.HTTP_200_OK)
@version("2025-04-01-preview")
async def get_document(document_id: int):
    return {"document_id": document_id}

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@version("2025-05-01")
async def delete_document(document_id: int):
    return None
