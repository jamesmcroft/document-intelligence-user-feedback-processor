from fastapi import FastAPI

app = FastAPI(
    title="Feedback Service",
    description="Feedback Service API",
    version="0.1.0"
)

# Include routes from each feature API module
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

# Entry point for running with 'python -m app.main'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
