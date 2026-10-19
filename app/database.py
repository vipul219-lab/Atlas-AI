import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "atlas_db")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2500)
db = client[MONGO_DB_NAME]
users_collection = db["users"]
sessions_collection = db["sessions"]
chat_history_collection = db["chat_history"]

_use_memory_store = False
_memory_users = {}
_memory_sessions = {}
_memory_chats = []


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, expected_digest = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100_000
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)


def init_db():
    global _use_memory_store
    try:
        client.admin.command("ping")
        users_collection.create_index([("username", ASCENDING)], unique=True)
        sessions_collection.create_index([("token", ASCENDING)], unique=True)
        chat_history_collection.create_index(
            [("username", ASCENDING), ("created_at", DESCENDING)]
        )
    except ServerSelectionTimeoutError:
        _use_memory_store = True
        print("MongoDB is unavailable; using temporary in-memory accounts and chat history.")
    seed_user("admin", "admin123", "admin")
    seed_user("demo_user", "user123", "user")


def seed_user(username: str, password: str, role: str):
    if _use_memory_store:
        if username not in _memory_users:
            _memory_users[username] = {
                "username": username,
                "password_hash": hash_password(password),
                "role": role,
            }
        return
    if not users_collection.find_one({"username": username}):
        users_collection.insert_one({
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
            "created_at": datetime.now(timezone.utc),
        })


def get_user_by_username(username: str):
    if _use_memory_store:
        return _memory_users.get(username)
    return users_collection.find_one({"username": username})


def create_user_record(username: str, password: str, role: str) -> bool:
    if _use_memory_store:
        if username in _memory_users:
            return False
        _memory_users[username] = {
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
        }
        return True
    try:
        users_collection.insert_one({
            "username": username,
            "password_hash": hash_password(password),
            "role": role,
            "created_at": datetime.now(timezone.utc),
        })
    except DuplicateKeyError:
        return False
    return True


def create_session(username: str, role: str) -> str:
    token = secrets.token_urlsafe(32)
    if _use_memory_store:
        _memory_sessions[token] = {"username": username, "role": role}
        return token
    sessions_collection.insert_one({
        "token": token,
        "username": username,
        "role": role,
        "created_at": datetime.now(timezone.utc),
    })
    return token


def get_session_user(token: str):
    if _use_memory_store:
        return _memory_sessions.get(token)
    session = sessions_collection.find_one({"token": token})
    if not session:
        return None
    return {"username": session["username"], "role": session["role"]}


def save_chat_message(username: str, role: str, mode: str, user_message: str, answer: str):
    chat = {
        "username": username,
        "role": role,
        "mode": mode,
        "user_message": user_message,
        "answer": answer,
        "created_at": datetime.now(timezone.utc),
    }
    if _use_memory_store:
        _memory_chats.append(chat)
        return
    chat_history_collection.insert_one(chat)


def get_recent_chats(username: str, limit: int = 50):
    if _use_memory_store:
        chats = [chat.copy() for chat in _memory_chats if chat["username"] == username]
        chats = chats[-limit:]
        for chat in chats:
            chat["created_at"] = chat["created_at"].isoformat()
        return chats
    chats = list(
        chat_history_collection.find({"username": username}, {"_id": 0})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
    chats.reverse()
    for chat in chats:
        chat["created_at"] = chat["created_at"].isoformat()
    return chats
