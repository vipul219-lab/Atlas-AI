# Atlas AI Gateway

Atlas is a local-first, multi-model AI gateway. It provides one authenticated interface for chat, code assistance, PDF analysis, image generation, and video generation while keeping the application and data under local control.

Atlas does not train models. It routes requests to existing models through a common FastAPI backend:

```text
React frontend -> FastAPI gateway -> Ollama or vLLM for text tasks
                                  -> FLUX server for images
                                  -> video diffusion server for videos
```

## Why Atlas Exists

Cloud AI services are not suitable for every private, restricted, or offline environment. Atlas demonstrates how an organization can provide controlled AI access through a local gateway instead of sending every prompt and document to a public API.

The internship version focused on serving language models with vLLM. This independent Atlas version extends that idea with both Ollama and vLLM support, MongoDB-backed accounts and chat history, a React interface, safety checks, and optional image/video model routes. Ollama makes the project easy to test on an ordinary laptop; vLLM is available for Linux systems with a suitable NVIDIA GPU.

## Features

- User and admin authentication
- Admin-created users and admins with unique usernames
- Secure password hashing and database-backed sessions
- Persistent chat history in MongoDB
- Chat and code generation
- PDF upload and document analysis
- Safety filtering for blocked prompts
- Optional FLUX image generation
- Optional video diffusion generation
- React frontend with mode navigation and conversation display
- FastAPI Swagger documentation
- Docker Compose for the application and MongoDB
- Ollama and vLLM provider selection

## Repository Layout

```text
atlas/
|- app/                  FastAPI backend
|  |- main.py            API routes
|  |- model_client.py    Ollama, vLLM, image, and video clients
|  |- database.py        MongoDB access and chat storage
|  |- auth.py            Session authentication
|  |- documents.py       PDF text extraction
|  |- models.py          Request validation
|  `- safety.py          Prompt safety checks
|- atlas-ui/             React/Vite frontend
|- requirements.txt      Backend dependencies
|- Dockerfile            Backend image
|- docker-compose.yml    MongoDB, backend, and frontend services
`- README.md             Setup and testing instructions
```

## Requirements

- Docker Desktop, or Docker Engine with Compose
- Ollama for the easy local text-model demo, or Linux plus an NVIDIA GPU for vLLM
- Node.js and npm only when running the frontend outside Docker
- Internet access for the first package/model download

Model weights are intentionally not committed to GitHub or included in Docker images. Ollama, vLLM, and the diffusion servers download their own models locally.

## Fastest Test: Docker + Ollama

Run these commands from the Atlas root, the folder containing `docker-compose.yml`.

### 1. Start Ollama

Keep this terminal open:

```bash
ollama serve
```

### 2. Download the text model once

Open a second terminal:

```bash
ollama pull qwen3:4b
```

### 3. Start Atlas

Open a third terminal:

```bash
cd /path/to/atlas
docker compose up --build
```

This starts MongoDB, the FastAPI backend, and the React frontend. Ollama runs separately on the host computer.

### 4. Open the application

```text
http://localhost:5173
```

Backend health check: `http://localhost:9000/health`

Swagger documentation: `http://localhost:9000/docs`

Default accounts:

```text
Admin:     admin / admin123
Demo user: demo_user / user123
```

MongoDB starts automatically in Docker. Its data is kept in the `atlas_mongo_data` volume, so MongoDB does not need to be installed manually.

## Run Directly With Ollama

Use this when you do not want Docker. MongoDB is optional: if it is unavailable, Atlas uses temporary in-memory accounts and chat history that reset when the backend restarts.

Terminal 1:

```bash
ollama serve
ollama pull qwen3:4b
```

Terminal 2:

```bash
uvicorn app.main:app --reload --port 9000
```

Terminal 3:

```bash
cd atlas-ui
npm install
npm run dev
```

Open `http://localhost:5173`.

## Run With vLLM

Use vLLM on a Linux machine with an NVIDIA GPU. vLLM downloads the model from Hugging Face on first use. A Hugging Face token is needed only if the selected model requires authentication.

Start vLLM in one terminal:

```bash
vllm serve Qwen/Qwen3-4B --host 0.0.0.0 --port 8000
```

Check that it is ready:

```bash
curl http://127.0.0.1:8000/v1/models
```

Start the backend in another terminal:

```bash
export MODEL_PROVIDER=vllm
export VLLM_BASE_URL=http://127.0.0.1:8000/v1
uvicorn app.main:app --reload --port 9000
```

Start the frontend in a third terminal:

```bash
cd atlas-ui
npm install
npm run dev
```

vLLM handles Atlas chat, code, and document requests. It does not handle image or video generation.

## Image and Video Generation

Image and video generation are optional GPU features. They are not started by the main Docker Compose file.

### Image Generation

Atlas sends a text prompt to a separate FLUX server. The server can use `black-forest-labs/FLUX.1-schnell` and must expose:

```text
POST http://127.0.0.1:8010/generate
```

Expected response:

```json
{"image_url": "path-or-url-to-image"}
```

### Video Generation

Atlas sends a text prompt to a separate video diffusion server. A compatible model such as `Wan-AI/Wan2.1-T2V-1.3B` can be used. The server must expose:

```text
POST http://127.0.0.1:8020/generate
```

Expected response:

```json
{"video_url": "path-or-url-to-video"}
```

These servers must be installed and started separately on a suitable GPU machine. If they are not running, Atlas chat, code, and document features still work, but image/video requests return a service-unavailable error.

## API Routes

```text
GET  /                    Service information
GET  /health              Health check
POST /login               Create a session token
GET  /admin/stats         Admin-only request statistics
POST /admin/users         Admin-only user creation
POST /chat                Chat, code, image, or video request
POST /analyze/document    PDF analysis request
GET  /chat/history        Current user's saved conversations
```

Authenticated requests use:

```text
token: Bearer YOUR_SESSION_TOKEN
```

## Docker Commands

```bash
docker compose up --build       # build and start everything
docker compose up --build -d    # start in the background
docker compose ps                # show service status
docker compose down              # stop services
docker compose down -v           # stop and delete MongoDB data
```

Use `docker compose down -v` only when you intentionally want to delete stored accounts and chat history.

## Testing Checklist

1. Log in as `admin`.
2. Create a new user from the admin panel.
3. Log in with the new account.
4. Test Chat and Code modes.
5. Upload a text-based PDF and test Document mode.
6. Restart the containers and confirm the account and history remain.
7. Test an unsafe prompt and confirm it is blocked.
8. Test Image and Video only after their separate servers are running.

## Security Notes

The default credentials are for demonstration only. Before production use, replace them, move configuration into environment variables, use HTTPS, and add token expiry and proper secret management.

Do not commit passwords, API keys, Hugging Face tokens, `.env` files, model weights, `node_modules`, or Python cache files.
