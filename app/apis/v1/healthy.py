from fastapi import APIRouter

router = APIRouter(prefix="/healthy", tags=["healthy"])


@router.get("/")
async def health_check():
    return {"status": "healthy"}
