from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from server.api.location import router as router_location
from server.api.person import router as router_person
from server.api.risk import router as router_risk
from server.api.policy import router as router_policy
from server.api.config import router as router_config
from server.api.claim import router as router_claim
from server.api.payout import router as router_payout
from server.api.health import router as router_health
from server.config import settings
from server.error import NotFoundError
from server.utils import create_app, include_router
from util.logging import get_logger

logger = get_logger()
app = create_app(settings)

# link to api routers
include_router(app, router_policy, "add policy api")
include_router(app, router_risk, "add risk api")
include_router(app, router_config, "add config api")
include_router(app, router_person, "add person api")
include_router(app, router_location, "add location api")
include_router(app, router_claim, "add claim api")
include_router(app, router_payout, "add payout api")
# include_router(app, router_polygon, "add polygon api")
include_router(app, router_health, "add health api")

# root redirection
@app.get("/", include_in_schema=False)
async def redirect():
    logger.info("redirecting to /docs")
    return RedirectResponse("/docs")

# custom exception handlers
@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code = 404,
        content = {
            "message": f"NotFoundError: {str(exc)}"
        },
    )

@app.exception_handler(ValueError)
async def not_found_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code = 400,
        content = {
            "message": f"ValueError: {str(exc)}"
        },
    )

@app.exception_handler(Exception)
async def not_found_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code = 500,
        content = {
            "message": f"{exc.__class__.__name__}: {str(exc)}"
        },
    )
