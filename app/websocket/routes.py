import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.core.database import SessionLocal
from app.crud.member import get_member
from app.websocket.manager import manager
from asyncio import wait_for

router = APIRouter()


def websocket_auth(token: str, workspace_id: uuid.UUID, db: Session):
    payload = decode_access_token(token)
    if isinstance(payload, dict):
        try:
            user_id = uuid.UUID(payload["sub"])
        except (KeyError, ValueError, TypeError):
            return None
        return get_member(db, workspace_id, user_id)


@router.websocket("/ws/notifications")
async def notifications_endpoint(websocket: WebSocket):
    """Per-user notification channel. First-message auth (same as the board
    socket); the token identifies the user — no room/membership check needed."""
    await websocket.accept()
    user_id: uuid.UUID | None = None
    try:
        auth_message = await wait_for(websocket.receive_json(), timeout=15.0)
        if auth_message.get("type") != "auth":
            await websocket.send_json(
                {"type": "error", "detail": "First message must be auth"}
            )
            await websocket.close()
            return
        token = auth_message.get("token")
        payload = decode_access_token(token) if token else None
        if (
            isinstance(payload, dict)
            and payload.get("type") != "refresh"
            and payload.get("sub")
        ):
            try:
                user_id = uuid.UUID(payload["sub"])
            except (ValueError, TypeError):
                user_id = None
        if user_id is None:
            await websocket.send_json({"type": "error", "detail": "Unauthorized"})
            await websocket.close()
            return
        await manager.connect_user(websocket, user_id)
        await websocket.send_json(
            {"type": "success", "detail": "Notification channel authenticated"}
        )
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    except TimeoutError:
        await websocket.send_json({"type": "error", "detail": "timeout exceeded"})
        await websocket.close()
    finally:
        if user_id is not None:
            await manager.disconnect_user(websocket, user_id)


@router.websocket("/ws/workspaces/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: uuid.UUID):
    # accept connection
    await websocket.accept()
    # wait for authentication message and set timeout
    try:
        auth_message = await wait_for(websocket.receive_json(), timeout=15.0)

        if auth_message.get("type") != "auth":
            await websocket.send_json(
                {"type": "error", "detail": "First message must be auth"}
            )
            await websocket.close()
            return
        token = auth_message.get("token")
        if not token:
            await websocket.send_json(
                {"type": "error", "detail": "Missing authentication token"}
            )
            await websocket.close()
            return
        with SessionLocal() as db:
            member = websocket_auth(token, workspace_id, db)
        if member:
            await manager.connect(websocket, workspace_id)
            await websocket.send_json(
                {"type": "success", "detail": "Websocket authentication successful"}
            )
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break
        else:
            await websocket.send_json(
                {"type": "error", "detail": "Unauthorized Access"}
            )
            await websocket.close()
    except TimeoutError:
        await websocket.send_json({"type": "error", "detail": "timeout exceeded"})
        await websocket.close()
    finally:
        await manager.disconnect(websocket, workspace_id)


# on arrive validate token
# then check membership before adding connection to room
# also prepare for a disconnect error
