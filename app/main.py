import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import HOST, PORT, MODEL_NAME
from app.schemas import ChatRequest, AgentResponse
from app.agent.loop import run_agent_loop
from app.rag.retriever import retrieve_regulations
from app.database import get_member, search_catalog, get_all_study_rooms

app = FastAPI(title="LibDesk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "LibDesk API is running. Visit /docs for Swagger UI"}

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "model": MODEL_NAME,
        "proxy_configured": bool(os.getenv("OPENAI_BASE_URL"))
    }

@app.post("/api/chat", response_model=AgentResponse)
def chat(request: ChatRequest):
    try:
        return run_agent_loop(
            user_message=request.message,
            member_id=request.member_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search-rules")
def search_rules(q: str):
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="กรุณาระบุคำค้นหา")
    return retrieve_regulations(query=q)

@app.get("/api/member/{member_id}")
def get_member_info(member_id: str):
    member = get_member(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="ไม่พบข้อมูลสมาชิก")
    return member

@app.get("/api/catalog")
def get_catalog(q: str = ""):
    return search_catalog(q)

@app.get("/api/study-rooms")
def get_study_rooms():
    return get_all_study_rooms()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)

