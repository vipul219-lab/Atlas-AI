from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from app.auth import get_current_user, require_admin
from app.database import (
    create_session, create_user_record, get_recent_chats, get_user_by_username,
    init_db, save_chat_message, verify_password,
)
from app.documents import extract_pdf_text
from app.model_client import ask_text_model, generate_image, generate_video
from app.models import ChatRequest, CreateUserRequest, LoginRequest
from app.safety import is_safe_message
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


stats = {
    "total_requests": 0,
    "blocked_requests": 0,
    "document_requests": 0,
}



@app.get("/")
def home():
    return {"app": "ATLAS", "message": "Atlas backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest):
    user = get_user_by_username(request.username)

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_session(user["username"], user["role"])

    return {
        "access_token": token,
        "token_type": "Bearer",
        "role": user["role"],
    }


@app.get("/admin/stats")
def admin_stats(token: str = Header(default="")):
    user = get_current_user(token)
    require_admin(user)
    return stats


@app.post("/admin/users")
def create_user(request: CreateUserRequest, token: str = Header(default="")):
    admin = get_current_user(token)
    require_admin(admin)

    if get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    if not create_user_record(request.username, request.password, request.role):
        raise HTTPException(status_code=400, detail="Username already exists")

    return {
        "message": "User created",
        "username": request.username,
        "role": request.role,
    }


@app.post("/chat")
async def chat(request: ChatRequest, token: str = Header(default="")):
    user = get_current_user(token)
    stats["total_requests"] += 1

    if not is_safe_message(request.message):
        stats["blocked_requests"] += 1
        raise HTTPException(
            status_code=400,
            detail="This request is blocked by Atlas safety rules.",
        )

    if request.mode in ["chat", "code", "document"]:
      answer = await ask_text_model(request.message, request.mode)

    elif request.mode == "image":
      answer = await generate_image(request.message)

    elif request.mode == "video":
      answer = await generate_video(request.message)

    else:
      raise HTTPException(status_code=400, detail="Unsupported mode")

    save_chat_message(
        username=user["username"], role=user["role"], mode=request.mode,
        user_message=request.message, answer=answer,
    )

    return {
        "user": user["username"],
        "role": user["role"],
        "mode": request.mode,
        "user_message": request.message,
        "answer": answer,
    }


@app.post("/analyze/document")
async def analyze_document(
    token: str = Header(default=""),
    prompt: str = Form("Summarize this document and list key points."),
    file: UploadFile = File(...),
):
    user = get_current_user(token)
    stats["total_requests"] += 1
    stats["document_requests"] += 1

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported now")

    if not is_safe_message(prompt):
        stats["blocked_requests"] += 1
        raise HTTPException(
            status_code=400,
            detail="This request is blocked by Atlas safety rules.",
        )

    document_text = extract_pdf_text(file)

    if not document_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in PDF")

    message = f"{prompt}\n\nDocument text:\n{document_text[:12000]}"
    answer = await ask_text_model(message, "document")
    save_chat_message(
        username=user["username"], role=user["role"], mode="document",
        user_message=prompt, answer=answer,
    )

    return {
        "user": user["username"],
        "role": user["role"],
        "filename": file.filename,
        "answer": answer,
    }


@app.get("/chat/history")
def chat_history(token: str = Header(default="")):
    user = get_current_user(token)
    return {"user": user["username"], "history": get_recent_chats(user["username"])}
