# workspace_backend.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, uuid, json
from typing import Dict, List

app = FastAPI()

# ---------------- CONFIG ----------------
BASE_STORAGE = "cloud_storage"
os.makedirs(BASE_STORAGE, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
        allow_origins=["*"],
            allow_credentials=True,
                allow_methods=["*"],
                    allow_headers=["*"],
                    )

                    # ---------------- IN-MEMORY DB ----------------
                    users = {}
                    workspaces = {}
                    connections: Dict[str, List[WebSocket]] = {}

                    # ---------------- HELPERS ----------------
                    def save_file(workspace_id, file: UploadFile):
                        folder = f"{BASE_STORAGE}/{workspace_id}"
                            os.makedirs(folder, exist_ok=True)
                                file_id = str(uuid.uuid4())
                                    path = f"{folder}/{file_id}_{file.filename}"
                                        with open(path, "wb") as f:
                                                f.write(file.file.read())
                                                    return path

                                                    async def broadcast(workspace_id, message):
                                                        if workspace_id in connections:
                                                                for ws in connections[workspace_id]:
                                                                            await ws.send_text(json.dumps(message))

                                                                            # ---------------- AUTH ----------------
                                                                            @app.post("/login")
                                                                            def login(username: str = Form(...)):
                                                                                user_id = str(uuid.uuid4())
                                                                                    users[user_id] = username
                                                                                        return {"user_id": user_id, "username": username}

                                                                                        # ---------------- WORKSPACE ----------------
                                                                                        @app.post("/workspace/create")
                                                                                        def create_workspace(name: str = Form(...), owner: str = Form(...)):
                                                                                            wid = str(uuid.uuid4())
                                                                                                workspaces[wid] = {
                                                                                                        "name": name,
                                                                                                                "owner": owner,
                                                                                                                        "messages": []
                                                                                                                            }
                                                                                                                                return {"workspace_id": wid}

                                                                                                                                # ---------------- TEXT MESSAGE ----------------
                                                                                                                                @app.post("/message/text")
                                                                                                                                async def send_text(
                                                                                                                                    workspace_id: str = Form(...),
                                                                                                                                        sender: str = Form(...),
                                                                                                                                            content: str = Form(...)
                                                                                                                                            ):
                                                                                                                                                msg = {
                                                                                                                                                        "type": "text",
                                                                                                                                                                "sender": sender,
                                                                                                                                                                        "content": content
                                                                                                                                                                            }
                                                                                                                                                                                workspaces[workspace_id]["messages"].append(msg)
                                                                                                                                                                                    await broadcast(workspace_id, msg)
                                                                                                                                                                                        return {"status": "sent"}

                                                                                                                                                                                        # ---------------- FILE / IMAGE / VOICE ----------------
                                                                                                                                                                                        @app.post("/message/file")
                                                                                                                                                                                        async def send_file(
                                                                                                                                                                                            workspace_id: str = Form(...),
                                                                                                                                                                                                sender: str = Form(...),
                                                                                                                                                                                                    file: UploadFile = File(...)
                                                                                                                                                                                                    ):
                                                                                                                                                                                                        path = save_file(workspace_id, file)
                                                                                                                                                                                                            msg = {
                                                                                                                                                                                                                    "type": "file",
                                                                                                                                                                                                                            "sender": sender,
                                                                                                                                                                                                                                    "filename": file.filename,
                                                                                                                                                                                                                                            "path": path
                                                                                                                                                                                                                                                }
                                                                                                                                                                                                                                                    workspaces[workspace_id]["messages"].append(msg)
                                                                                                                                                                                                                                                        await broadcast(workspace_id, msg)
                                                                                                                                                                                                                                                            return {"status": "uploaded"}

                                                                                                                                                                                                                                                            # ---------------- FILE DOWNLOAD ----------------
                                                                                                                                                                                                                                                            @app.get("/download")
                                                                                                                                                                                                                                                            def download(path: str):
                                                                                                                                                                                                                                                                return FileResponse(path)

                                                                                                                                                                                                                                                                # ---------------- REALTIME WEBSOCKET ----------------
                                                                                                                                                                                                                                                                @app.websocket("/ws/{workspace_id}")
                                                                                                                                                                                                                                                                async def websocket_endpoint(ws: WebSocket, workspace_id: str):
                                                                                                                                                                                                                                                                    await ws.accept()
                                                                                                                                                                                                                                                                        if workspace_id not in connections:
                                                                                                                                                                                                                                                                                connections[workspace_id] = []
                                                                                                                                                                                                                                                                                    connections[workspace_id].append(ws)

                                                                                                                                                                                                                                                                                        try:
                                                                                                                                                                                                                                                                                                while True:
                                                                                                                                                                                                                                                                                                            await ws.receive_text()
                                                                                                                                                                                                                                                                                                                except WebSocketDisconnect:
                                                                                                                                                                                                                                                                                                                        connections[workspace_id].remove(ws)