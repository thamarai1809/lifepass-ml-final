from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.responses import FileResponse,HTMLResponse

from pydantic import BaseModel

from src.share_manager import (
    create_share_table,
    create_share,
    get_share,
    revoke_share,
    share_html,
)

import uuid
import joblib
import os
import shutil

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

from src.privacy_firewall import analyze_privacy

from src.database import (
    create_tables,
    insert_document,
    get_documents,
    get_document,
    delete_document
)


# ==========================================
# LifePass API
# ==========================================

app = FastAPI(
    title="LifePass ML API",
    description="Document classification and management API",
    version="1.0"
)


# ==========================================
# Initialize Database
# ==========================================

create_tables()
create_share_table()

# ==========================================
# Load ML Model
# ==========================================

model = joblib.load(
    "models/lifepass_classifier.joblib"
)


# ==========================================
# Upload Directory
# ==========================================

UPLOAD_DIR = os.path.abspath(
    "uploads"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ==========================================
# Request Model
# ==========================================

class DocumentRequest(BaseModel):

    text: str


# ==========================================
# Home
# ==========================================

@app.get("/")
def home():

    return {
        "message":
        "LifePass ML API is running"
    }


# ==========================================
# Text Classification
# ==========================================

@app.post("/predict")
def predict(
    request: DocumentRequest
):

    prediction = model.predict(
        [request.text]
    )[0]

    probabilities = model.predict_proba(
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


# ==========================================
# Upload + Process Document
# ==========================================

@app.post("/predict-document")
async def predict_document(
    file: UploadFile = File(...)
):

    # --------------------------------------
    # Allowed file types
    # --------------------------------------

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".pdf"
    ]

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Use JPG, JPEG, PNG or PDF."
            )
        )

    # --------------------------------------
    # Original filename
    # --------------------------------------

    original_filename = os.path.basename(
        file.filename
    )

    # --------------------------------------
    # Unique stored filename
    # --------------------------------------

    unique_filename = (
        f"{uuid.uuid4().hex[:8]}_"
        f"{original_filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    # --------------------------------------
    # Save original document
    # --------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        # ==================================
        # OCR
        # ==================================

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

        # ==================================
        # Classification
        # ==================================

        prediction = model.predict(
            [extracted_text]
        )[0]

        probabilities = model.predict_proba(
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

        # ==================================
        # Expiry Detection
        # ==================================

        expiry_date = extract_expiry_date(
            extracted_text
        )

        print(
            "Expiry Date:",
            expiry_date
        )

        # ==================================
        # Field Extraction
        # ==================================

        fields = extract_fields(
            extracted_text,
            prediction
        )

        print(
            "Extracted Fields:",
            fields
        )

        # ==================================
        # Renewal Status
        # ==================================

        renewal_status = get_renewal_status(
            expiry_date
        )

        print(
            "Renewal Status:",
            renewal_status
        )

        # ==================================
        # Save to Database
        # ==================================

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

        # ==================================
        # Return Result
        # ==================================

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
            extracted_text
        }

    except Exception:

        # ----------------------------------
        # Remove uploaded file if processing
        # fails
        # ----------------------------------

        if os.path.exists(
            file_path
        ):

            os.remove(
                file_path
            )

        raise


# ==========================================
# Get All Documents
# ==========================================

# ==========================================
# Get All Documents
# ==========================================
@app.post("/privacy-check")
def privacy_check(request: dict):
    fields = request.get("fields", {})

    if not isinstance(fields, dict):
        raise HTTPException(
            status_code=400,
            detail="Fields must be provided as a dictionary."
        )

    result = analyze_privacy(fields)

    return result

@app.get("/documents")
def documents():

    all_documents = get_documents()

    return {
        "documents": all_documents
    }

    return {

        "documents":
        get_documents()

    }


# ==========================================
# Get One Document
# ==========================================

@app.get(
    "/documents/{document_id}"
)
def document_details(
    document_id: int
):

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return document


# ==========================================
# View Original Document
# ==========================================

@app.get(
    "/documents/{document_id}/file"
)
def document_file(
    document_id: int
):

    document = get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    file_path = document.get(
        "file_path"
    )

# --------------------------------------
# Resolve file path for local/Docker use
# --------------------------------------

    if file_path:

    # If the database contains an old
    # Windows host path, extract only
    # the uploads-relative portion.
        normalized_path = file_path.replace(
            "\\",
            "/"
        )

        if "/uploads/" in normalized_path:

            filename = normalized_path.split(
                "/uploads/",
                1
            )[1]

            file_path = os.path.join(
                "/app",
                "uploads",
                filename
            )

        elif normalized_path.startswith(
            "uploads/"
        ):

            file_path = os.path.join(
                "/app",
                normalized_path
            )

# --------------------------------------
# Verify physical file
# --------------------------------------

    if (
        not file_path
        or not os.path.exists(file_path)
    ):

        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    # --------------------------------------
    # Determine media type
    # --------------------------------------

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

    # --------------------------------------
    # Open in browser
    # --------------------------------------

    return FileResponse(

        path=file_path,

        media_type=media_type,

        headers={
            "Content-Disposition":
            (
                "inline; "
                f'filename="{document["filename"]}"'
            )
        }
    )


# ==========================================
# Delete Document
# ==========================================

@app.delete(
    "/documents/{document_id}"
)
def remove_document(
    document_id: int
):

    # --------------------------------------
    # Delete database record
    # and retrieve file path
    # --------------------------------------

    file_path = delete_document(
        document_id
    )

    if file_path is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    # --------------------------------------
    # Delete physical file
    # --------------------------------------

    if (
        file_path
        and os.path.exists(file_path)
    ):

        os.remove(
            file_path
        )

    return {

        "message":
        "Document deleted successfully."

    }

class ShareRequest(BaseModel):
    document_id: int
    fields: list[dict]
    expires_hours: int = 24


@app.post("/shares")
def create_secure_share(request: ShareRequest):

    if not request.fields:
        raise HTTPException(
            status_code=400,
            detail="Select at least one field before creating a share link."
        )

    if request.expires_hours not in [1, 6, 24, 72]:
        raise HTTPException(
            status_code=400,
            detail="Share duration must be 1, 6, 24 or 72 hours."
        )

    document = get_document(request.document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    token, expires_at = create_share(
        document_id=request.document_id,
        document_name=document.get("filename", "Document"),
        fields=request.fields,
        expires_hours=request.expires_hours,
    )

    share_url = f"http://127.0.0.1:8000/share/{token}"

    return {
        "token": token,
        "share_url": share_url,
        "expires_at": expires_at,
        "document_id": request.document_id,
        "fields_count": len(request.fields),
    }


@app.get("/share/{token}", response_class=HTMLResponse)
def view_secure_share(token: str):

    share = get_share(token)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share link not found."
        )

    return HTMLResponse(
        content=share_html(share),
        status_code=200
    )


@app.delete("/shares/{token}")
def revoke_secure_share(token: str):

    share = get_share(token)

    if not share:
        raise HTTPException(
            status_code=404,
            detail="Share link not found."
        )

    if share.get("status") == "revoked":
        return {
            "message": "Share link is already revoked."
        }

    revoke_share(token)

    return {
        "message": "Share access revoked successfully."
    }