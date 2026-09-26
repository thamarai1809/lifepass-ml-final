import sqlite3
import os


# ==========================================
# Database Configuration
# ==========================================

DATABASE = "/app/data/lifepass.db"


# ==========================================
# Get Database Connection
# ==========================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# Create Tables
# ==========================================

def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------
    # Documents table
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT NOT NULL,

            file_path TEXT,

            document_type TEXT,

            confidence REAL,

            document_number TEXT,

            holder_name TEXT,

            date_of_birth TEXT,

            issue_date TEXT,

            expiry_date TEXT,

            renewal_status TEXT,

            days_remaining INTEGER,

            extracted_text TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------
    # Add file_path to older databases
    # --------------------------------------

    cursor.execute(
        "PRAGMA table_info(documents)"
    )

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "file_path" not in columns:

        cursor.execute("""
            ALTER TABLE documents
            ADD COLUMN file_path TEXT
        """)

    connection.commit()

    connection.close()


# ==========================================
# Insert Document
# ==========================================

def insert_document(
    filename,
    file_path,
    document_type,
    confidence,
    fields,
    expiry_date,
    renewal_status,
    extracted_text
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO documents (

            filename,
            file_path,
            document_type,
            confidence,
            document_number,
            holder_name,
            date_of_birth,
            issue_date,
            expiry_date,
            renewal_status,
            days_remaining,
            extracted_text

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        filename,

        file_path,

        document_type,

        confidence,

        fields.get(
            "document_number"
        ),

        fields.get(
            "holder_name"
        ),

        fields.get(
            "date_of_birth"
        ),

        fields.get(
            "issue_date"
        ),

        expiry_date,

        renewal_status.get(
            "status"
        ),

        renewal_status.get(
            "days_remaining"
        ),

        extracted_text
    ))

    document_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return document_id


# ==========================================
# Get All Documents
# ==========================================

def get_documents():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM documents
        ORDER BY created_at DESC
    """)

    documents = cursor.fetchall()

    connection.close()

    return [
        dict(document)
        for document in documents
    ]


# ==========================================
# Get One Document
# ==========================================

def get_document(
    document_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM documents
        WHERE id = ?
    """, (
        document_id,
    ))

    document = cursor.fetchone()

    connection.close()

    if document:

        return dict(document)

    return None


# ==========================================
# Delete Document
# ==========================================

def delete_document(
    document_id
):

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------
    # Get file path before deleting record
    # --------------------------------------

    cursor.execute("""
        SELECT file_path
        FROM documents
        WHERE id = ?
    """, (
        document_id,
    ))

    document = cursor.fetchone()

    if not document:

        connection.close()

        return None

    file_path = document["file_path"]

    # --------------------------------------
    # Delete database record
    # --------------------------------------

    cursor.execute("""
        DELETE FROM documents
        WHERE id = ?
    """, (
        document_id,
    ))

    connection.commit()

    connection.close()

    return file_path


# ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    create_tables()

    print(
        "LifePass database initialized successfully."
    )