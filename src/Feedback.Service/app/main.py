from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.common.app_settings import app_settings
from app.common.observability.setup import setup_observability
from app.features.model_training.api.documents_api import router as model_training_documents_router
from app.common.versioning.versioning import VersionedOpenAPI

# Initialize Observability
setup_observability()

# Initialize API
app = FastAPI(
    title=app_settings.app_name,
    description=app_settings.app_desc,
    version="1.0.0",
    docs_url=None
)
FastAPIInstrumentor.instrument_app(app)

# Initialize Versioning
openapi = VersionedOpenAPI(app)

# Include routes from each feature API module
app.include_router(model_training_documents_router, prefix="/model_training", tags=["model_training"])
# app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

# Optionally add middleware, exception handlers, startup/shutdown events here
# For example:
# from starlette.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

openapi.configure_spec_routes()

app.openapi = openapi.configure_schema

# Entry point for running with 'python -m app.main'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
