from fastapi import APIRouter

from app.modules.comparison.router import router as comparison_router
from app.modules.diagram.router import router as diagram_router
from app.modules.general.router import router as general_router
from app.modules.input.router import router as input_router
from app.modules.irac.router import router as irac_router
from app.modules.mvp.router import router as mvp_router
from app.modules.retrieval.router import router as retrieval_router
from app.modules.usage.router import router as usage_router
from app.modules.user.router import router as user_router
from app.modules.verification.router import router as verification_router


api_routers: list[APIRouter] = [
    input_router,
    general_router,
    mvp_router,
    retrieval_router,
    irac_router,
    diagram_router,
    verification_router,
    comparison_router,
    usage_router,
    user_router,
]
