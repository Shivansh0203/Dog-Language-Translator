import secrets
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect


router = APIRouter(
    prefix="/api/mobile",
    tags=["mobile-camera"],
)


# Temporary in-memory session store.
# This is intentionally simple for the development phase.
# Later, it can be moved to Redis/database for production.
mobile_sessions: Dict[str, dict] = {}
websocket_connections: Dict[str, Dict[str, WebSocket]] = {}
SESSION_EXPIRY_SECONDS = 10 * 60


def cleanup_expired_sessions():
    now = time.time()

    expired = [
        session_id
        for session_id, session in mobile_sessions.items()
        if now - session["created_at"] > SESSION_EXPIRY_SECONDS
    ]

    for session_id in expired:
        mobile_sessions.pop(session_id, None)


@router.post("/session")
def create_mobile_session():
    """
    Creates a temporary pairing session between
    the PawAI laptop browser and the mobile browser.
    """

    cleanup_expired_sessions()

    session_id = secrets.token_urlsafe(9)
    session_token = secrets.token_urlsafe(24)

    mobile_sessions[session_id] = {
        "token": session_token,
        "created_at": time.time(),
        "laptop_connected": False,
        "mobile_connected": False,
        "recording": False,
        "status": "waiting",
    }

    return {
        "session_id": session_id,
        "session_token": session_token,
        "status": "waiting",
        "expires_in": SESSION_EXPIRY_SECONDS,
    }


@router.get("/session/{session_id}")
def get_mobile_session(session_id: str, token: str):
    """
    Allows the mobile browser to verify that
    the requested pairing session exists.
    """

    cleanup_expired_sessions()

    session = mobile_sessions.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Mobile camera session not found or expired.",
        )

    if not secrets.compare_digest(session["token"], token):
        raise HTTPException(
            status_code=403,
            detail="Invalid mobile camera session token.",
        )

    return {
        "session_id": session_id,
        "status": session["status"],
        "laptop_connected": session["laptop_connected"],
        "mobile_connected": session["mobile_connected"],
        "recording": session["recording"],
    }

@router.post("/session/{session_id}/submit")
async def submit_recording(session_id: str, token: str):
    cleanup_expired_sessions()

    session = mobile_sessions.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Mobile camera session not found or expired."
        )

    if not secrets.compare_digest(session["token"], token):
        raise HTTPException(
            status_code=403,
            detail="Invalid mobile camera session token."
        )

    session["recording"] = True
    session["status"] = "submitted"

    connections = websocket_connections.get(session_id, {})
    laptop_socket = connections.get("laptop")

    if laptop_socket is not None:
        try:
            await laptop_socket.send_json({
                "type": "recording_submitted",
                "session_id": session_id,
                "status": "submitted"
            })
        except Exception:
            pass

    return {
        "success": True,
        "message": "Recording submitted successfully.",
        "status": "submitted"
    }
@router.websocket("/ws/{session_id}")
async def mobile_camera_websocket(
    websocket: WebSocket,
    session_id: str,
    role: str,
):
    """
    WebRTC signaling channel.

    The laptop and mobile browser connect to the same
    session ID with different roles.

    role=laptop
    role=mobile
    """

    await websocket.accept()

    session = mobile_sessions.get(session_id)

    if session is None:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found or expired."
        })

        await websocket.close()
        return

    if role not in {"laptop", "mobile"}:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid WebSocket role."
        })

        await websocket.close()
        return

    # Create connection container for this session
    if session_id not in websocket_connections:
        websocket_connections[session_id] = {}

    # Replace an old connection from the same role
    old_connection = websocket_connections[
        session_id
    ].get(role)

    if old_connection is not None:
        try:
            await old_connection.close()
        except Exception:
            pass

    websocket_connections[session_id][role] = websocket

    # Update session state
    if role == "laptop":
        session["laptop_connected"] = True

    if role == "mobile":
        session["mobile_connected"] = True

    # Tell the connecting client that its socket is ready
    await websocket.send_json({
        "type": "connected",
        "role": role,
        "session_id": session_id
    })

    # If both sides are connected, notify both
    connections = websocket_connections[session_id]

    if "laptop" in connections and "mobile" in connections:

        session["status"] = "connected"

        for client_role, client_socket in connections.items():

            try:
                await client_socket.send_json({
                    "type": "peer_connected",
                    "peer": (
                        "mobile"
                        if client_role == "laptop"
                        else "laptop"
                    )
                })
            except Exception:
                pass

    try:

        while True:

            message = await websocket.receive_json()

            # Forward WebRTC signaling messages
            # to the other participant.
            connections = websocket_connections.get(
                session_id,
                {}
            )

            target_role = (
                "mobile"
                if role == "laptop"
                else "laptop"
            )

            target_socket = connections.get(target_role)

            if target_socket is not None:

                await target_socket.send_json({
                    **message,
                    "from": role
                })

    except WebSocketDisconnect:

        pass

    finally:

        connections = websocket_connections.get(
            session_id,
            {}
        )

        if connections.get(role) is websocket:
            connections.pop(role, None)

        if role == "laptop":
            session["laptop_connected"] = False

        if role == "mobile":
            session["mobile_connected"] = False

        if not connections:
            websocket_connections.pop(
                session_id,
                None
            )
            mobile_sessions.pop(
                session_id,
                None
            )