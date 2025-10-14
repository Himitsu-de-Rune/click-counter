from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(bind=database.engine)

connections = set()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Утилиты ----------
def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_total_count(db: Session):
    return sum(u.count for u in db.query(models.User).all())

# ---------- Маршруты ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")

@app.post("/register")
async def register(username: str = Form(...), db: Session = Depends(get_db)):
    user = get_user(db, username)
    if user:
        return {"ok": True}
    db_user = models.User(username=username)
    db.add(db_user)
    db.commit()
    return {"ok": True}

@app.post("/action")
async def action(
    request: Request,
    username: str = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user(db, username)
    if not user:
        return {"error": "User not found"}

    if action == "inc":
        user.count += 1
    elif action == "dec":
        user.count -= 1
    elif action == "reset":
        user.count = 0

    db.commit()

    total = get_total_count(db)
    for conn in list(connections):
        try:
            await conn.send_json({"total": total})
        except:
            connections.remove(conn)

    return {"user_count": user.count, "total": total}

@app.get("/stats")
async def stats(username: str, db: Session = Depends(get_db)):
    user = get_user(db, username)
    if not user:
        return {"user_count": 0, "total": get_total_count(db)}
    return {"user_count": user.count, "total": get_total_count(db)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)
