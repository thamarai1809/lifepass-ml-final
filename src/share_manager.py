import os
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from html import escape

DB_PATH = os.path.abspath("lifepass.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_share_table():
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secure_shares (
                token TEXT PRIMARY KEY,
                document_id INTEGER NOT NULL,
                document_name TEXT NOT NULL,
                fields_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def create_share(document_id, document_name, fields, expires_hours):
    create_share_table()

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=int(expires_hours))

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO secure_shares
            (token, document_id, document_name, fields_json,
             created_at, expires_at, revoked)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                token,
                int(document_id),
                document_name,
                json.dumps(fields, ensure_ascii=False),
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return token, expires_at.isoformat()


def get_share(token):
    create_share_table()

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM secure_shares WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    share = dict(row)
    share["fields"] = json.loads(share.pop("fields_json"))

    if share["revoked"]:
        share["status"] = "revoked"
        return share

    expires_at = datetime.fromisoformat(share["expires_at"])
    if expires_at <= datetime.now(timezone.utc):
        share["status"] = "expired"
    else:
        share["status"] = "active"

    return share


def revoke_share(token):
    create_share_table()

    conn = _connect()
    try:
        cursor = conn.execute(
            "UPDATE secure_shares SET revoked = 1 WHERE token = ?",
            (token,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def share_html(share):
    status = share["status"]

    if status != "active":
        title = "Share Unavailable"
        message = {
            "expired": "This LifePass share link has expired.",
            "revoked": "This LifePass share link has been revoked.",
        }.get(status, "This LifePass share link is unavailable.")

        return f"""
        <!doctype html>
        <html>
        <head>
            <meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>{escape(title)} - LifePass</title>
            <style>
                body {{
                    margin: 0;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: #f5f7fb;
                    color: #172033;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }}
                .card {{
                    max-width: 560px;
                    margin: 24px;
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 18px;
                    padding: 32px;
                    box-shadow: 0 10px 30px rgba(0,0,0,.08);
                }}
                h1 {{ margin-top: 0; }}
                p {{ color: #667085; line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class='card'>
                <h1>LifePass</h1>
                <h2>{escape(title)}</h2>
                <p>{escape(message)}</p>
            </div>
        </body>
        </html>
        """

    rows = "".join(
        f"""
        <tr>
            <td>{escape(str(item.get('field', 'Field')))}</td>
            <td>{escape(str(item.get('value', '')))}</td>
        </tr>
        """
        for item in share["fields"]
    )

    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1'>
        <title>LifePass Secure Share</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #f5f7fb;
                color: #172033;
            }}
            .wrap {{ max-width: 760px; margin: 60px auto; padding: 0 20px; }}
            .card {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                padding: 32px;
                box-shadow: 0 10px 30px rgba(0,0,0,.08);
            }}
            .brand {{ font-size: 34px; font-weight: 800; margin-bottom: 4px; }}
            .subtitle {{ color: #667085; margin-bottom: 28px; }}
            .notice {{
                background: #ecfdf3;
                border: 1px solid #abefc6;
                color: #067647;
                padding: 14px 16px;
                border-radius: 10px;
                margin-bottom: 24px;
            }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ text-align: left; padding: 14px; border-bottom: 1px solid #eaecf0; }}
            th {{ color: #667085; font-size: 13px; text-transform: uppercase; }}
            td {{ font-size: 15px; }}
            .footer {{ color: #98a2b3; font-size: 13px; margin-top: 24px; }}
        </style>
    </head>
    <body>
        <div class='wrap'>
            <div class='card'>
                <div class='brand'>LifePass</div>
                <div class='subtitle'>Privacy-controlled document sharing</div>

                <div class='notice'>
                    Only the information explicitly selected by the owner is shown here.
                </div>

                <h2>{escape(share['document_name'])}</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Shared Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>

                <div class='footer'>
                    This share link expires at {escape(share['expires_at'])}.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
