from .contacts import router as contacts_router
from .deals import router as deals_router
from .pipelines import router as pipelines_router
from .activities import router as activities_router

__all__ = ["contacts_router", "deals_router", "pipelines_router", "activities_router"]
