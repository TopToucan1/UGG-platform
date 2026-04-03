import bcrypt
import jwt
import os
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId
from database import db

JWT_ALGORITHM = "HS256"
router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_jwt_secret():
    return os.environ["JWT_SECRET"]


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_role(request: Request, roles: list) -> dict:
    user = await get_current_user(request)
    if user.get("role") not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return user


# --- Models ---
class LoginInput(BaseModel):
    email: str
    password: str

class RegisterInput(BaseModel):
    email: str
    password: str
    name: str
    role: Optional[str] = "operator"

class ForgotPasswordInput(BaseModel):
    email: str

class ResetPasswordInput(BaseModel):
    token: str
    new_password: str


# --- Brute Force ---
async def check_brute_force(ip: str, email: str):
    identifier = f"{ip}:{email}"
    record = await db.login_attempts.find_one({"identifier": identifier})
    if record and record.get("count", 0) >= 5:
        locked_until = record.get("locked_until")
        if locked_until and datetime.now(timezone.utc) < locked_until:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 15 minutes.")
        else:
            await db.login_attempts.delete_one({"identifier": identifier})


async def record_failed_login(ip: str, email: str):
    identifier = f"{ip}:{email}"
    record = await db.login_attempts.find_one({"identifier": identifier})
    if record:
        new_count = record.get("count", 0) + 1
        update = {"$set": {"count": new_count, "last_attempt": datetime.now(timezone.utc)}}
        if new_count >= 5:
            update["$set"]["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.login_attempts.update_one({"identifier": identifier}, update)
    else:
        await db.login_attempts.insert_one({
            "identifier": identifier,
            "count": 1,
            "last_attempt": datetime.now(timezone.utc),
        })


async def clear_failed_logins(ip: str, email: str):
    await db.login_attempts.delete_many({"identifier": f"{ip}:{email}"})


# --- Routes ---
@router.post("/register")
async def register(inp: RegisterInput, response: Response):
    email = inp.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": email,
        "password_hash": hash_password(inp.password),
        "name": inp.name,
        "role": inp.role if inp.role in ["admin", "operator", "engineer", "state_regulator", "distributor_admin", "retailer_viewer", "manufacturer_viewer"] else "operator",
        "tenant_id": None,
        "distributor_id": None,
        "retailer_id": None,
        "manufacturer_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    access = create_access_token(user_id, email, user_doc["role"])
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)

    return {"id": user_id, "email": email, "name": inp.name, "role": user_doc["role"]}


@router.post("/login")
async def login(inp: LoginInput, request: Request, response: Response):
    email = inp.email.lower().strip()
    ip = request.client.host if request.client else "unknown"

    await check_brute_force(ip, email)

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(inp.password, user["password_hash"]):
        await record_failed_login(ip, email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await clear_failed_logins(ip, email)
    user_id = str(user["_id"])

    access = create_access_token(user_id, email, user.get("role", "operator"))
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)

    return {
        "id": user_id,
        "email": email,
        "name": user.get("name", ""),
        "role": user.get("role", "operator"),
        "tenant_id": user.get("tenant_id"),
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    return user


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user_id = str(user["_id"])
        access = create_access_token(user_id, user["email"], user.get("role", "operator"))
        response.set_cookie(key="access_token", value=access, httponly=True, secure=True, samesite="none", max_age=86400, path="/")
        return {"message": "Token refreshed"}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/forgot-password")
async def forgot_password(inp: ForgotPasswordInput):
    email = inp.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": "If the email exists, a reset link has been sent"}
    token = secrets.token_urlsafe(32)
    await db.password_reset_tokens.insert_one({
        "token": token,
        "user_id": str(user["_id"]),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used": False,
    })
    import logging
    logging.getLogger(__name__).info(f"Password reset link: /reset-password?token={token}")
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(inp: ResetPasswordInput):
    record = await db.password_reset_tokens.find_one({"token": inp.token, "used": False})
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if datetime.now(timezone.utc) > record["expires_at"]:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    await db.users.update_one(
        {"_id": ObjectId(record["user_id"])},
        {"$set": {"password_hash": hash_password(inp.new_password)}},
    )
    await db.password_reset_tokens.update_one({"_id": record["_id"]}, {"$set": {"used": True}})
    return {"message": "Password reset successfully"}


# --- Seed Admin ---
async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@ugg.io")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "UGG Admin",
            "role": "admin",
            "tenant_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )

    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("identifier")

    # Seed 4-tier route portal users
    route_users = [
        {"email": "regulator@state.nv.gov", "name": "State Regulator", "role": "state_regulator", "password": "SASG2S2026"},
        {"email": "ops@starlightgaming.com", "name": "Starlight Distributor Admin", "role": "distributor_admin", "password": "SASG2S2026"},
        {"email": "manager@joesbargrill.com", "name": "Joe's Bar Retailer", "role": "retailer_viewer", "password": "SASG2S2026"},
        {"email": "support@aristocrat.com", "name": "Aristocrat Manufacturer", "role": "manufacturer_viewer", "password": "SASG2S2026"},
    ]
    for ru in route_users:
        existing = await db.users.find_one({"email": ru["email"]})
        if not existing:
            await db.users.insert_one({
                "email": ru["email"],
                "password_hash": hash_password(ru["password"]),
                "name": ru["name"],
                "role": ru["role"],
                "tenant_id": None,
                "distributor_id": None,
                "retailer_id": None,
                "manufacturer_id": ru.get("manufacturer_id"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
