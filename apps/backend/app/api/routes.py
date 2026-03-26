from fastapi import APIRouter

from app.core.settings import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.members.router import router as members_router
from app.modules.ministries.router import router as ministries_router
from app.modules.events.router import router as events_router
from app.modules.volunteers.router import router as volunteers_router
from app.modules.attendance.router import router as attendance_router
from app.modules.notifications.router import router as notifications_router

api_router = APIRouter(prefix=settings.API_PREFIX)

# Domain routers (most are still scaffolds; auth is implemented in Step 2).
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(members_router)
api_router.include_router(ministries_router)
api_router.include_router(events_router)
api_router.include_router(volunteers_router)
api_router.include_router(attendance_router)
api_router.include_router(notifications_router)

