from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("")
async def health() -> JSONResponse:
    return JSONResponse({"message": "health check success"})
