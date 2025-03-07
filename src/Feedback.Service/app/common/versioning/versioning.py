import functools
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from typing import Optional, Callable, Any, Set

DEFAULT_API_VERSION = "2025-01-01"

def version(*versions: str) -> Callable:
    """
    Decorator to attach supported API versions to an endpoint.
    Example usage:
        @version("2025-01-01", "2024-12-01-preview")
    """
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "__versions__"):
            setattr(func, "__versions__", set())
        func.__versions__.update(versions)
        return func
    return decorator


def get_api_version(api_version: Optional[str] = Query(
    None, alias="api-version", description="API version")) -> str:
    """
    Returns the API version provided via the query parameter.
    If not provided, it defaults to the latest version.
    """
    return api_version or DEFAULT_API_VERSION


def get_valid_api_versions(app: FastAPI) -> Set[str]:
    """
    Iterate over all routes in the app and return a set of all API versions
    that have been defined via the @version decorator (or auto-assigned).
    """
    valid_versions = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            endpoint = route.endpoint
            versions = getattr(endpoint, "__versions__", set())
            valid_versions.update(versions)
    return valid_versions


def get_versioned_openapi(app: FastAPI, version: str):
    """
    Generate an OpenAPI schema filtered to include only routes
    that support the given API version.
    """
    valid_versions = get_valid_api_versions(app)
    if version not in valid_versions:
        raise HTTPException(
            status_code=404,
            detail=f"API version '{version}' is not a valid API version. "
                   f"Valid versions: {sorted(valid_versions)}"
        )

    versioned_routes = []
    for route in app.routes:
        # Only filter routes that are instances of APIRoute.
        if isinstance(route, APIRoute):
            endpoint = route.endpoint
            supported_versions = getattr(endpoint, "__versions__", {DEFAULT_API_VERSION})
            if version in supported_versions:
                versioned_routes.append(route)

    if not versioned_routes:
        raise HTTPException(status_code=404, detail=f"No routes available for version {version}")

    return get_openapi(
        title=f"{app.title} (version {version})",
        version=version,
        routes=versioned_routes,
    )


class VersionedRoute(APIRoute):
    """
    Custom route that inspects the request for an "api-version" query parameter.
    It compares that version against the versions declared via the @version decorator.
    If the endpoint does not support the requested version, a 404 is returned.
    """
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()
        endpoint = self.endpoint

        if not hasattr(endpoint, "__versions__"):
            setattr(endpoint, "__versions__", {DEFAULT_API_VERSION})

        async def versioned_handler(request: Request) -> Any:
            # Get the query parameters and the version; default to latest if missing.
            params = dict(request.query_params)
            version = params.get("api-version", DEFAULT_API_VERSION)

            # Access the endpoint function to get its supported versions.
            supported_versions: Set[str] = getattr(endpoint, "__versions__")
            if version not in supported_versions:
                raise HTTPException(
                    status_code=404,
                    detail=f"API version '{version}' is not supported for this endpoint. "
                           f"Supported versions: {sorted(supported_versions)}"
                )
            return await original_handler(request)
        return versioned_handler

class VersionedOpenAPI:
    def __init__(self, app: FastAPI):
        self._app = app

    def configure_schema(self):
        openapi_schema = get_openapi(
            title=self._app.title,
            version=self._app.version,
            openapi_version=self._app.openapi_version,
            description=self._app.description,
            routes=self._app.routes
        )

        version_param = {
            "name": "api-version",
            "in": "query",
            "description": "API version",
            "required": False,
            "schema": {
                "type": "string",
                "default": DEFAULT_API_VERSION
            }
        }

        for path_item in openapi_schema.get("paths", {}).values():
            for operation in path_item.values():
                # If not already present, add the version query parameter.
                params = operation.setdefault("parameters", [])
                if not any(p.get("name") == "api-version" for p in params):
                    params.append(version_param)

        self._app.openapi_schema = openapi_schema
        return self._app.openapi_schema

    def configure_spec_routes(self):
        router = APIRouter()

        @router.get("/openapi/{api_version}", include_in_schema=False)
        def openapi_spec(api_version: str):
            """
            Return a version-specific OpenAPI specification.
            """
            return get_versioned_openapi(self._app, api_version)

        self._app.include_router(router)
