from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # so agent settings (DECIDER_API_KEY, AWS_*) in backend/.env reach os.environ
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, agent_status, auth, community, org, posts
from app.core.config import settings

app = FastAPI(title="Problem 360 API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(agent_status.router)
app.include_router(org.router)
app.include_router(community.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
