from fastapi import APIRouter

router = APIRouter(prefix="/user")


@router.get("/")
async def get_user():
    return {"message": "Hello, World!"}
