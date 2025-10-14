from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uuid

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

user_counts = {}
USER_COOKIE_NAME = "user_id"

def get_user_id(request: Request, response: Response) -> str:
    user_id = request.cookies.get(USER_COOKIE_NAME)
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key=USER_COOKIE_NAME, value=user_id, path="/")
    return user_id

@app.get("/")
async def get_index(request: Request, response: Response):
    get_user_id(request, response)
    return FileResponse("static/index.html")

@app.get("/count")
async def get_count(request: Request, response: Response):
    user_id = get_user_id(request, response)
    return {"count": user_counts.get(user_id, 0)}

@app.post("/click")
async def add_click(request: Request, response: Response):
    user_id = get_user_id(request, response)
    user_counts[user_id] = user_counts.get(user_id, 0) + 1
    return {"count": user_counts[user_id]}
