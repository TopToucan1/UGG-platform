from fastapi import APIRouter, Request
from database import db
from auth import get_current_user

router = APIRouter(prefix="/api/commands", tags=["commands"])


@router.get("")
async def list_commands(request: Request, status: str = None, limit: int = 50, skip: int = 0):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    commands = await db.commands.find(query, {"_id": 0}).sort("issued_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.commands.count_documents(query)
    return {"commands": commands, "total": total}


@router.get("/{command_id}")
async def get_command(request: Request, command_id: str):
    await get_current_user(request)
    cmd = await db.commands.find_one({"id": command_id}, {"_id": 0})
    if not cmd:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Command not found")
    return cmd
