from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import get_current_user
from schemas.schemas import MessageRequest

router = APIRouter(tags=["Messages"])


@router.get("/messages")
def get_messages(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        rows = db.execute(
            text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
                   FROM messages m
                   JOIN users u ON m.sender_id = u.user_id
                   WHERE m.receiver_id = :uid OR m.sender_id = :uid
                   ORDER BY m.sent_at DESC LIMIT 50"""),
            {"uid": user["user_id"]},
        ).fetchall()
    except Exception:
        try:
            rows = db.execute(
                text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
                       FROM messages m
                       JOIN users u ON m.sender_id = u.user_id
                       WHERE m.receiver_id = :uid OR m.sender_id = :uid
                       ORDER BY m.created_at DESC LIMIT 50"""),
                {"uid": user["user_id"]},
            ).fetchall()
        except Exception:
            rows = db.execute(
                text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
                       FROM messages m
                       JOIN users u ON m.sender_id = u.user_id
                       WHERE m.receiver_id = :uid OR m.sender_id = :uid
                       ORDER BY 1 DESC LIMIT 50"""),
                {"uid": user["user_id"]},
            ).fetchall()

    messages_list = []
    for r in rows:
        d = dict(r._mapping)
        if "message_id" not in d or d["message_id"] is None:
            d["message_id"] = d.get("msg_id")
        if "msg_id" not in d or d["msg_id"] is None:
            d["msg_id"] = d.get("message_id")
        if not d.get("sent_at"):
            d["sent_at"] = d.get("created_at") or ""
        if not d.get("created_at"):
            d["created_at"] = d.get("sent_at") or ""
        messages_list.append(d)

    return {"success": True, "messages": messages_list}


@router.post("/messages", status_code=201)
def send_message(
    body: MessageRequest,
    db:   Session = Depends(get_db),
    user: dict    = Depends(get_current_user),
):
    db.execute(
        text("""INSERT INTO messages (sender_id, receiver_id, project_id, subject, body)
               VALUES (:sender_id, :receiver_id, :project_id, :subject, :body)"""),
        {
            "sender_id":   user["user_id"],
            "receiver_id": body.receiver_id,
            "project_id":  body.project_id,
            "subject":     body.subject,
            "body":        body.body,
        },
    )
    db.execute(
        text("""INSERT INTO alerts (user_id, project_id, alert_type, title, message, severity)
               VALUES (:uid, :pid, 'feedback', :title, :msg, 'info')"""),
        {
            "uid":   body.receiver_id,
            "pid":   body.project_id,
            "title": f"New Message: {(body.subject or 'No Subject')[:60]}",
            "msg":   body.body[:200],
        },
    )
    db.commit()
    return {"success": True, "message": "Message sent."}
