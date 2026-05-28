from fastapi.responses import Response
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
app = FastAPI()
import bleach
import uuid
import os
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import filetype
from fastapi import Depends
from fastapi import Header, HTTPException



ALLOWED_TAGS = ["b", "i", "u", "em", "strong"]
templates = Jinja2Templates(directory="templates")
templates = Jinja2Templates(directory="templates")

users = {
    "alice": {"username": "alice", "role": "user"},
    "bob": {"username": "bob", "role": "user"},
    "admin": {"username": "admin", "role": "admin"},
}

files_db = [
    {"id": 1, "name": "alice_report.pdf", "owner": "alice", "size": 120},
    {"id": 2, "name": "bob_report.pdf", "owner": "bob", "size": 200},
    {"id": 3, "name": "admin_report.pdf", "owner": "admin", "size": 999},
]


def get_current_user(x_user: str = Header(...)):
    if x_user not in users:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return users[x_user]


@app.middleware("http")
async def add_csp_header(request: Request, call_next):
    response = await call_next(request)

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self';"
    )

    return response


def sanitize_comment(text: str):
    return bleach.clean(text, tags=ALLOWED_TAGS, strip=True)
comments = []
@app.post("/comments", response_class=HTMLResponse)
async def post_comment(request: Request, text: str = Form(...)):
    clean_text = sanitize_comment(text)

    comments.append(clean_text)

    return templates.TemplateResponse(
        "comments.html",
        {
            "request": request,
            "comments": comments
        }
    )

@app.get("/comments", response_class=HTMLResponse)
async def get_comments(request: Request):
    return templates.TemplateResponse(
        "comments.html",
        {
            "request": request,
            "comments": comments
        }
    )



def check_file_permissions(file_id: int, user=Depends(get_current_user)):
    file = next((f for f in files_db if f["id"] == file_id), None)

    if not file:
        raise HTTPException(status_code=404, detail="Not Found")

    if user["role"] == "admin":
        return file

    if file["owner"] == user["username"]:
        return file

    raise HTTPException(status_code=404, detail="Not Found")
@app.get("/files/{file_id}")
def get_file(file_id: int, file=Depends(check_file_permissions)):
    return file
@app.delete("/files/{file_id}")
def delete_file(file_id: int, user=Depends(get_current_user)):
    global files_db

    file = next((f for f in files_db if f["id"] == file_id), None)

    if not file:
        raise HTTPException(status_code=404, detail="Not Found")

    if user["role"] != "admin" and file["owner"] != user["username"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    files_db = [f for f in files_db if f["id"] != file_id]

    return {"msg": "deleted"}
@app.get("/files/all")
def all_files(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return files_db
@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...), request: Request = None):
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")


    kind = filetype.guess(contents)
    if not kind or kind.mime not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")


    file_id = str(uuid.uuid4())
    ext = ".jpg" if kind.mime == "image/jpeg" else ".png"
    path = f"storage/{file_id}{ext}"

    with open(path, "wb") as f:
        f.write(contents)


    files_db.append({
        "id": file_id,
        "owner": request.headers.get("X-User"),
        "original_name": file.filename,
        "path": path,
        "size": len(contents)
    })

    return {"msg": "uploaded", "id": file_id}
@app.get("/files/{file_id}/download")
def download_file(file_id: str, request: Request):
    user = request.headers.get("X-User")

    file = next((f for f in files_db if f["id"] == file_id), None)

    if not file:
        raise HTTPException(status_code=404)

    if user != "admin" and file["owner"] != user:
        raise HTTPException(status_code=404)

    return FileResponse(
        file["path"],
        filename=file["original_name"],
        media_type="application/octet-stream"
    )
