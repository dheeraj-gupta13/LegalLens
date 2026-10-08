from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def to_dict(self):
        return {"id": self.id, "email": self.email}


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="processing")  # processing|ready|failed
    page_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "filename": self.filename, "status": self.status,
                "pages": self.page_count, "created_at": self.uploaded_at.isoformat() + "Z"}


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"), nullable=False)
    messages = db.relationship("Message", backref="session", order_by="Message.id",
                               cascade="all, delete-orphan")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_session.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # user|assistant
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "role": self.role, "content": self.content,
                "sources": self.sources or [], "created_at": self.created_at.isoformat() + "Z"}


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("document.id"), unique=True, nullable=False)
    result = db.Column(db.JSON, nullable=False)
