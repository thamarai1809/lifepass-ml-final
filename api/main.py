import os
import io
import uuid
import shutil
import traceback
import threading
from pathlib import Path

import joblib

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import (
    FileResponse,
    HTMLResponse
)

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel


# ============================================================
# LifePass internal modules
# ============================================================

from src.share_manager import (
    create_share_table,
    create_share,
    get_share,
    revoke_share,
    share_html,
)

from src.document_processor import (
    extract_text_from_file
)

from src.expiry_extractor import (
    extract_expiry_date
)

from src.field_extractor import (
    extract_fields
)

from src.renewal_checker import (
    get_renewal_status
)

from src.privacy_firewall import (
    analyze_privacy
)

from src.database import (
    create_tables,
    insert_document,
    get_documents,
    get_document,
    delete_document
)


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="LifePass ML API",
    description="Document classification and management API",
    version="1.1"
)


# ============================================================
# CORS
# ============================================================
#
# Useful if the frontend is deployed on Vercel.
#
# For Streamlit on Render, this is not normally required,
# but keeping it here makes the API frontend-independent.
#
# Set this Render environment variable if needed:
#
# FRONTEND_URL=https://your-frontend.vercel.app
#
# ============================================================

frontend_url = os.getenv(
    "FRONTEND_URL",
    "*"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if frontend_url == "*" else [frontend_url],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Public API URL
# ============================================================
#
# IMPORTANT:
#
# On Render set:
#
# PUBLIC_BASE_URL=https://lifepasss-api.onrender.com
#
# Locally it automatically falls back to localhost.
#
# Render may also provide RENDER_EXTERNAL_URL.
#
# ============================================================

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    os.getenv(
        "RENDER_EXTERNAL_URL",
        "http://127.0.0.1:8000"
    )
).rstrip("/")


# ============================================================
# Debug Version
# ============================================================

@app.get("/debug-version")
def debug_version():

    return {
        "version": "DEBUG-2026-09-26-FIXED-SHARING-DOWNLOAD",
        "message": "LifePass API with Render sharing/download fixes",
        "public_base_url": PUBLIC_BASE_URL,
        "upload_dir": UPLOAD_DIR if "UPLOAD_DIR" in globals() else None
    }


# ============================================================
# Database and ML model initialization
# ============================================================
#
# Do not let a missing model file or a temporary database problem
# crash the entire API process during import. The health endpoints
# should remain available so Render can report useful diagnostics.
#
# On Render, configure LIFEPASS_MODEL_PATH if the model is not at
# the default path relative to this file.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = Path(
    os.getenv(
        "LIFEPASS_MODEL_PATH",
        str(BASE_DIR / "models" / "lifepass_classifier.joblib")
    )
).expanduser()

_model = None
_model_load_error = None
_model_lock = threading.Lock()

_database_init_error = None

try:
    create_tables()
    create_share_table()
except Exception as exc:
    _database_init_error = str(exc)
    print("DATABASE INITIALIZATION FAILED:")
    traceback.print_exc()


def get_model():
    """Load the classifier once, on first use, and return clear API errors."""
    global _model, _model_load_error

    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        try:
            if not MODEL_PATH.is_file():
                raise FileNotFoundError(
                    f"Model file not found at {MODEL_PATH}. "
                    "Check that the model is committed/deployed and "
                    "LIFEPASS_MODEL_PATH is correct."
                )

            _model = joblib.load(str(MODEL_PATH))
            _model_load_error = None
            print(f"ML model loaded successfully from: {MODEL_PATH}")
            return _model

        except Exception as exc:
            _model_load_error = str(exc)
            print(f"ML MODEL LOAD FAILED: {_model_load_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=503,
                detail=(
                    "The classification model is unavailable. "
                    "Check the API Render logs and LIFEPASS_MODEL_PATH."
                )
            ) from exc


def ensure_database_ready():
    """Fail explicitly instead of returning an unhelpful proxy error."""
    if _database_init_error:
        raise HTTPException(
            status_code=503,
            detail=(
                "The database could not be initialized. "
                "Check the API Render logs for the database initialization error."
            )
        )


# ============================================================
# Upload Directory
# ============================================================
#
# Render:
#     /tmp/lifepass/uploads
#
# Local:
#     Can be overridden using:
#
#     LIFEPASS_UPLOAD_DIR=uploads
#
# ============================================================

UPLOAD_DIR = os.getenv(
    "LIFEPASS_UPLOAD_DIR",
    "/tmp/lifepass/uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# Helper: Resolve Stored File Path
# ============================================================

def resolve_file_path(stored_path):
    """
    Resolve a document path stored in SQLite.

    Handles:
        - Current Render paths
        - Local Windows paths
        - Old /app/uploads paths
        - Relative uploads paths

    The physical file is always looked for inside UPLOAD_DIR
    when the original stored path does not exist.
    """

    if not stored_path:
        return None

    stored_path = str(
        stored_path
    )

    # --------------------------------------------------------
    # If the exact stored path exists, use it.
    # --------------------------------------------------------

    if os.path.isfile(stored_path):

        return stored_path

    # --------------------------------------------------------
    # Normalize Windows/Linux separators
    # --------------------------------------------------------

    normalized = stored_path.replace(
        "\\",
        "/"
    )

    # --------------------------------------------------------
    # Extract only the filename.
    #
    # This is important because old SQLite records may contain:
    #
    # D:/projects/lifepass-ml/uploads/abc_test.png
    #
    # while Render stores the actual file at:
    #
    # /tmp/lifepass/uploads/abc_test.png
    # --------------------------------------------------------

    filename = os.path.basename(
        normalized
    )

    if not filename:
        return None

    # --------------------------------------------------------
    # Look for the file in the current upload directory.
    # --------------------------------------------------------

    candidate = os.path.join(
        UPLOAD_DIR,
        filename
    )

    if os.path.isfile(candidate):

        return candidate

    return None


# ============================================================
# Request Model
# ============================================================

class DocumentRequest(BaseModel):

    text: str


# ============================================================
# Share Request
# ============================================================

class ShareRequest(BaseModel):

    document_id: int

    fields: list[dict]

    expires_hours: int = 24


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():

    return {
        "message": "LifePass ML API is running"
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health():
    # Lightweight liveness check: does not load the model or query the database.
    return {
        "status": "ok",
        "service": "LifePass ML API",
        "version": app.version
    }


@app.get("/ready")
def readiness():
    # Diagnostics for deployment troubleshooting; avoids exposing stack traces.
    return {
        "status": "ready" if not _database_init_error else "degraded",
        "database_initialized": _database_init_error is None,
        "database_error": bool(_database_init_error),
        "model_loaded": _model is not None,
        "model_path": str(MODEL_PATH),
        "model_error": bool(_model_load_error),
        "upload_dir_exists": os.path.isdir(UPLOAD_DIR) if "UPLOAD_DIR" in globals() else False
    }


# ============================================================
# Text Classification
# ============================================================

@app.post("/predict")
def predict(
    request: DocumentRequest
):

    classifier = get_model()

    if not hasattr(classifier, "predict"):
        raise HTTPException(
            status_code=503,
            detail="The configured model does not support prediction."
        )

    if not hasattr(classifier, "predict_proba"):
        raise HTTPException(
            status_code=503,
            detail=(
                "The configured model does not support predict_proba; "
                "use a probability-capable classifier or update the API response."
            )
        )

    prediction = classifier.predict(
        [request.text]
    )[0]

    probabilities = classifier.predict_proba(
        [request.text]
    )[0]

    confidence = max(
        probabilities
    )

    return {

        "document_type":
            prediction,

        "confidence":
            round(
                float(confidence),
                4
            )
    }


# ============================================================
# Upload + Process Document
# ============================================================

@app.post("/predict-document")
def predict_document(
    file: UploadFile = File(...)
):

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".pdf"
    ]

    extension = os.path.splitext(
        file.filename or ""
    )[1].lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Use JPG, JPEG, PNG or PDF."
            )
        )

    submitted_filename = (file.filename or "").replace("\\", "/")
    original_filename = os.path.basename(submitted_filename).strip()

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must have a valid filename."
        )

    ensure_database_ready()

    unique_filename = (
        f"{uuid.uuid4().hex[:8]}_"
        f"{original_filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    print(
        "\n=========================================="
    )

    print(
        "DOCUMENT PROCESSING STARTED"
    )

    print(
        "Original filename:",
        original_filename
    )

    print(
        "Stored filename:",
        unique_filename
    )

    print(
        "Upload directory:",
        UPLOAD_DIR
    )

    print(
        "Full file path:",
        file_path
    )

    print(
        "=========================================="
    )

    try:

        # ----------------------------------------------------
        # Save uploaded file
        # ----------------------------------------------------

        # Stream the upload to disk with a hard size limit. Avoid loading
        # the entire file into RAM, which can trigger worker restarts on Render.
        max_upload_bytes = int(os.getenv("LIFEPASS_MAX_UPLOAD_MB", "15")) * 1024 * 1024
        total_bytes = 0

        with open(file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File is too large. Maximum allowed size is "
                            f"{max_upload_bytes // (1024 * 1024)} MB."
                        )
                    )

                buffer.write(chunk)

        print(
            "File saved:",
            os.path.exists(file_path)
        )

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        extracted_text = extract_text_from_file(
            file_path
        )

        print(
            "\n========== OCR TEXT =========="
        )

        print(
            extracted_text
        )

        if not extracted_text.strip():

            raise HTTPException(
                status_code=400,
                detail=(
                    "No text could be extracted "
                    "from the document."
                )
            )

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        classifier = get_model()

        if not hasattr(classifier, "predict") or not hasattr(classifier, "predict_proba"):
            raise HTTPException(
                status_code=503,
                detail=(
                    "The configured model must support predict and predict_proba."
                )
            )

        prediction = classifier.predict(
            [extracted_text]
        )[0]

        probabilities = classifier.predict_proba(
            [extracted_text]
        )[0]

        confidence = max(
            probabilities
        )

        print(
            "\nDocument Type:",
            prediction
        )

        print(
            "Confidence:",
            round(
                float(confidence),
                4
            )
        )

        # ----------------------------------------------------
        # Expiry Detection
        # ----------------------------------------------------

        expiry_date = extract_expiry_date(
            extracted_text
        )

        print(
            "Expiry Date:",
            expiry_date
        )

        # ----------------------------------------------------
        # Field Extraction
        # ----------------------------------------------------

        fields = extract_fields(
            extracted_text,
            prediction
        )

        print(
            "Extracted Fields:",
            fields
        )

        # ----------------------------------------------------
        # Renewal Status
        # ----------------------------------------------------

        renewal_status = get_renewal_status(
            expiry_date
        )

        print(
            "Renewal Status:",
            renewal_status
        )

        # ----------------------------------------------------
        # Save database record
        # ----------------------------------------------------

        document_id = insert_document(

            filename=original_filename,

            file_path=file_path,

            document_type=prediction,

            confidence=float(
                confidence
            ),

            fields=fields,

            expiry_date=expiry_date,

            renewal_status=renewal_status,

            extracted_text=extracted_text
        )

        print(
            "Saved Document ID:",
            document_id
        )

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return {

            "document_id":
                document_id,

            "filename":
                original_filename,

            "document_type":
                prediction,

            "confidence":
                round(
                    float(confidence),
                    4
                ),

            "expiry_date":
                expiry_date,

            "renewal_status":
                renewal_status,

            "fields":
                fields,

            "extracted_text":
                extracted_text,

            # Useful for frontend
            "view_url":
                (
                    f"{PUBLIC_BASE_URL}"
                    f"/documents/{document_id}/file"
                ),

            "download_url":
                (
                    f"{PUBLIC_BASE_URL}"
                    f"/documents/{document_id}/download"
                )
        }

    except HTTPException:

        # Preserve intended HTTP errors such as 400/404.
        #
        # DO NOT convert them into 500 errors.

        if os.path.exists(file_path):

            os.remove(
                file_path
            )

        raise

    except Exception as e:

        print(
            "\n========== PREDICT DOCUMENT ERROR =========="
        )

        traceback.print_exc()

        print(
            "============================================"
        )

        if os.path.exists(file_path):

            os.remove(
                file_path
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document processing failed. Check the API Render logs "
                "for the detailed traceback."
            )
        ) from e


# ============================================================
# Privacy Check
# ============================================================

@app.post("/privacy-check")
def privacy_check(
    request: dict
):

    fields = request.get(
        "fields",
        {}
    )

    if not isinstance(
        fields,
        dict
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Fields must be provided "
                "as a dictionary."
            )
        )

    try:
        result = analyze_privacy(fields)
        return result
    except Exception as exc:
        print("PRIVACY CHECK FAILED:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Privacy analysis failed. Check the API Render logs."
        ) from exc


# ============================================================
# Get All Documents
# ============================================================

@app.get("/documents")
def documents():
    ensure_database_ready()

    return {
        "documents":
            get_documents()
    }


# ============================================================
# Get One Document
# ============================================================

@app.get(
    "/documents/{document_id}"
)
def document_details(
    document_id: int
):
    ensure_database_ready()

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return document


# ============================================================
# View Original Document
# ============================================================

@app.get(
    "/documents/{document_id}/file"
)
def document_file(
    document_id: int
):
    ensure_database_ready()

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    file_path = resolve_file_path(
        document.get("file_path")
    )

    print(
        "\n========== FILE VIEW =========="
    )

    print(
        "Document ID:",
        document_id
    )

    print(
        "Database path:",
        document.get("file_path")
    )

    print(
        "Resolved path:",
        file_path
    )

    print(
        "Exists:",
        bool(
            file_path and
            os.path.exists(file_path)
        )
    )

    if not file_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "Original document file "
                "is not available on this server."
            )
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()

    media_types = {

        ".pdf":
            "application/pdf",

        ".png":
            "image/png",

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg"
    }

    media_type = media_types.get(
        extension,
        "application/octet-stream"
    )

    return FileResponse(

        path=file_path,

        media_type=media_type,

        headers={
            "Content-Disposition": "inline"
        }
    )


# ============================================================
# Download Original Document
# ============================================================

@app.get(
    "/documents/{document_id}/download"
)
def download_document(
    document_id: int
):
    ensure_database_ready()

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    file_path = resolve_file_path(
        document.get("file_path")
    )

    print(
        "\n========== FILE DOWNLOAD =========="
    )

    print(
        "Document ID:",
        document_id
    )

    print(
        "Database path:",
        document.get("file_path")
    )

    print(
        "Resolved path:",
        file_path
    )

    if not file_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "Original document file "
                "is not available on this server."
            )
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()

    media_types = {

        ".pdf":
            "application/pdf",

        ".png":
            "image/png",

        ".jpg":
            "image/jpeg",

        ".jpeg":
            "image/jpeg"
    }

    media_type = media_types.get(
        extension,
        "application/octet-stream"
    )

    return FileResponse(

        path=file_path,

        media_type=media_type,

        filename=document["filename"],

        headers={
            "Content-Disposition":
                (
                    "attachment; "
                    f'filename="{document["filename"]}"'
                )
        }
    )


# ============================================================
# Delete Document
# ============================================================

@app.delete(
    "/documents/{document_id}"
)
def remove_document(
    document_id: int
):
    ensure_database_ready()

    # --------------------------------------------------------
    # Get database record before deleting it.
    # --------------------------------------------------------

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    stored_path = document.get(
        "file_path"
    )

    # Resolve before database deletion.
    physical_path = resolve_file_path(
        stored_path
    )

    # --------------------------------------------------------
    # Delete database record
    # --------------------------------------------------------

    delete_document(
        document_id
    )

    # --------------------------------------------------------
    # Delete physical file
    # --------------------------------------------------------

    if physical_path and os.path.exists(
        physical_path
    ):

        os.remove(
            physical_path
        )

    return {

        "message":
            "Document deleted successfully."
    }


# ============================================================
# Create Temporary Secure Share
# ============================================================

@app.post("/shares")
def create_secure_share(
    request: ShareRequest
):
    ensure_database_ready()

    # --------------------------------------------------------
    # Validate fields
    # --------------------------------------------------------

    if not request.fields:

        raise HTTPException(
            status_code=400,
            detail=(
                "Select at least one field "
                "before creating a share link."
            )
        )

    # --------------------------------------------------------
    # Validate duration
    # --------------------------------------------------------

    if request.expires_hours not in [
        1,
        6,
        24,
        72
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Share duration must be "
                "1, 6, 24 or 72 hours."
            )
        )

    # --------------------------------------------------------
    # Find document
    # --------------------------------------------------------

    document = get_document(
        request.document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # --------------------------------------------------------
    # Verify original file exists
    # --------------------------------------------------------

    file_path = resolve_file_path(
        document.get("file_path")
    )

    if not file_path:

        raise HTTPException(
            status_code=404,
            detail=(
                "Original document file "
                "is not available on this server."
            )
        )

    # --------------------------------------------------------
    # Create share token
    # --------------------------------------------------------

    token, expires_at = create_share(

        document_id=request.document_id,

        document_name=document.get(
            "filename",
            "Document"
        ),

        fields=request.fields,

        expires_hours=request.expires_hours
    )

    # ========================================================
    # IMPORTANT FIX
    # ========================================================
    #
    # NEVER use:
    #
    # http://127.0.0.1:8000
    #
    # on the deployed application.
    #
    # Use the Render public URL.
    #
    # ========================================================

    share_url = (
        f"{PUBLIC_BASE_URL}"
        f"/share/{token}"
    )

    print(
        "\n========== SHARE CREATED =========="
    )

    print(
        "Document ID:",
        request.document_id
    )

    print(
        "Token:",
        token
    )

    print(
        "Public Base URL:",
        PUBLIC_BASE_URL
    )

    print(
        "Share URL:",
        share_url
    )

    print(
        "Expires:",
        expires_at
    )

    return {

        "token":
            token,

        "share_url":
            share_url,

        "expires_at":
            expires_at,

        "document_id":
            request.document_id,

        "fields_count":
            len(request.fields)
    }


# ============================================================
# View Secure Share
# ============================================================

@app.get(
    "/share/{token}",
    response_class=HTMLResponse
)
def view_secure_share(
    token: str
):

    share = get_share(
        token
    )

    if not share:

        raise HTTPException(
            status_code=404,
            detail="Share link not found."
        )

    return HTMLResponse(
        content=share_html(
            share
        ),
        status_code=200
    )


# ============================================================
# Revoke Secure Share
# ============================================================

@app.delete(
    "/shares/{token}"
)
def revoke_secure_share(
    token: str
):

    share = get_share(
        token
    )

    if not share:

        raise HTTPException(
            status_code=404,
            detail="Share link not found."
        )

    if share.get("status") == "revoked":

        return {
            "message":
                "Share link is already revoked."
        }

    revoke_share(
        token
    )

    return {

        "message":
            "Share access revoked successfully."
    }
