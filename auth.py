"""
auth.py — Passlib/bcrypt şifre hashing + itsdangerous imzalı cookie session.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from passlib.context import CryptContext
from fastapi import Cookie, HTTPException, status

from db import get_conn

# ── Crypto setup ───────────────────────────────────────────────────────────────
SECRET_KEY: str = os.environ.get("SECRET_KEY", os.urandom(32).hex())
_signer = URLSafeTimedSerializer(SECRET_KEY, salt="session")
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 gün


# ── Password helpers ───────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain[:72])


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain[:72], hashed)


# ── Session cookie ─────────────────────────────────────────────────────────────
def make_session_cookie(user_id: int) -> str:
    return _signer.dumps(user_id)


def decode_session_cookie(token: str) -> Optional[int]:
    try:
        return int(_signer.loads(token, max_age=SESSION_MAX_AGE))
    except (BadSignature, SignatureExpired, ValueError):
        return None


# ── DB helpers ─────────────────────────────────────────────────────────────────
def create_user(email: str, plain_password: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users(email, hashed_pw) VALUES(?,?)",
            (email.strip().lower(), hash_password(plain_password)),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Bu e-posta adresi zaten kayıtlı.")
    finally:
        conn.close()


def authenticate_user(email: str, plain_password: str) -> Optional[int]:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, hashed_pw FROM users WHERE email=?",
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    if not verify_password(plain_password, row["hashed_pw"]):
        return None
    return int(row["id"])


# ── FastAPI dependency ─────────────────────────────────────────────────────────
def get_current_user(session: Optional[str] = Cookie(default=None)) -> int:
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Giriş gerekli")
    user_id = decode_session_cookie(session)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz oturum")
    return user_id