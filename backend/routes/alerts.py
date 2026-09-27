from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from middleware.auth import get_current_user
from schemas.schemas import MessageRequest

router = APIRouter(tags=["Alerts & Messages"])


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.execute(
        text("SELECT * FROM alerts WHERE user_id=:uid ORDER BY triggered_at DESC LIMIT 50"),
        {"uid": user["user_id"]},
    ).fetchall()
    return {"success": True, "alerts": [dict(r._mapping) for r in rows]}


@router.patch("/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db.execute(
        text("UPDATE alerts SET is_read=1, read_at=CURRENT_TIMESTAMP WHERE alert_id=:aid AND user_id=:uid"),
        {"aid": alert_id, "uid": user["user_id"]},
    )
    db.commit()
    return {"success": True}


@router.patch("/alerts/read-all")
def mark_all_read(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db.execute(
        text("UPDATE alerts SET is_read=1, read_at=CURRENT_TIMESTAMP WHERE user_id=:uid"),
        {"uid": user["user_id"]},
    )
    db.commit()
    return {"success": True}


@router.get("/messages")
def get_messages(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.execute(
        text("""SELECT m.*, u.full_name AS sender_name, u.role AS sender_role
           FROM messages m
           JOIN users u ON m.sender_id=u.user_id
           WHERE m.receiver_id=:uid OR m.sender_id=:uid
           ORDER BY m.sent_at DESC LIMIT 50"""),
        {"uid": user["user_id"]},
    ).fetchall()
    return {"success": True, "messages": [dict(r._mapping) for r in rows]}


@router.post("/messages")
def send_message(body: MessageRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db.execute(
        text("INSERT INTO messages (sender_id,receiver_id,project_id,subject,body) VALUES (:sid,:rid,:pid,:subject,:body)"),
        {"sid": user["user_id"], "rid": body.receiver_id, "pid": body.project_id, "subject": body.subject, "body": body.body},
    )
    db.execute(
        text("""INSERT INTO alerts (user_id,project_id,alert_type,title,message,severity)
           VALUES (:uid,:pid,'feedback',:title,:message,'info')"""),
        {
            "uid":     body.receiver_id,
            "pid":     body.project_id,
            "title":   f"Message from {user.get('full_name','Someone')}: {body.subject or 'No Subject'}",
            "message": body.body[:200],
        },
    )
    db.commit()
    return {"success": True, "message": "Message sent."}


@router.patch("/messages/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db.execute(
        text("UPDATE messages SET is_read=1 WHERE message_id=:mid AND receiver_id=:uid"),
        {"mid": message_id, "uid": user["user_id"]},
    )
    db.commit()
    return {"success": True}
