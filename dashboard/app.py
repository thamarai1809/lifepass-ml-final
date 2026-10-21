
import os
import time
from urllib.parse import urlparse, urlunparse

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =========================================================
# CONFIGURATION
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "https://lifepasss-api.onrender.com"
).strip().rstrip("/")

CONNECT_TIMEOUT = 15
READ_TIMEOUT = 90
UPLOAD_TIMEOUT = 300

TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="LifePass",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>
.stApp {
    background-color: #f5f7fb;
    color: #172033;
}
.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
.stApp p, .stApp label, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp button,
.stApp input, .stApp textarea {
    font-family: "Trebuchet MS", "Segoe UI", Arial, sans-serif;
}
.stApp h1 {
    font-size: 44px !important;
    font-weight: 800 !important;
    color: #172033 !important;
}
.stApp h2 {
    font-size: 29px !important;
    font-weight: 750 !important;
    color: #172033 !important;
}
.stApp h3 {
    font-size: 21px !important;
    font-weight: 700 !important;
    color: #172033 !important;
}
section[data-testid="stSidebar"] {
    background-color: #172033;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span {
    color: #172033 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background-color: #ffffff !important;
    color: #172033 !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
}
div[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 15px;
    padding: 15px;
    box-shadow: 0 3px 12px rgba(0,0,0,.04);
}
div[data-testid="stMetric"] label {
    color: #6b7280 !important;
}
div[data-testid="stMetricValue"] {
    color: #172033 !important;
    font-size: 27px;
    font-weight: 800;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff;
    border-radius: 15px;
    border: 1px solid #e5e7eb;
}
.stButton > button, .stDownloadButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    min-height: 40px !important;
}
div[data-testid="stExpander"] {
    background-color: #ffffff;
    border-radius: 10px;
    border: 1px solid #d1d5db;
}
textarea {
    color: #172033 !important;
    background-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HTTP SESSION
# =========================================================

@st.cache_resource
def get_http_session():
    session = requests.Session()

    # Retry only safe/idempotent requests automatically.
    # Never automatically repeat uploads, deletes, or share
    # creation, because the server may already have acted.
    retry = Retry(
        total=2,
        connect=2,
        read=0,
        status=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
        respect_retry_after_header=True,
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "LifePass-Frontend/2.0"})

    return session


HTTP = get_http_session()


# =========================================================
# API HELPERS
# =========================================================

def api_url(endpoint=""):
    return f"{API_URL}/{endpoint.lstrip('/')}"


def api_request(method, endpoint, **kwargs):
    """Make an API request and return the response.

    Raises requests exceptions for connection failures/timeouts.
    HTTP status codes are inspected by the calling function.
    """
    timeout = kwargs.pop(
        "timeout",
        (CONNECT_TIMEOUT, READ_TIMEOUT)
    )

    return HTTP.request(
        method,
        api_url(endpoint),
        timeout=timeout,
        **kwargs
    )


def parse_json_response(response):
    try:
        return response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        return None


def get_error_message(response):
    data = parse_json_response(response)

    if isinstance(data, dict):
        detail = data.get("detail") or data.get("message")
        if detail:
            return str(detail)[:2000]

    body = (response.text or "").strip()

    if response.status_code == 502:
        return (
            "Render returned HTTP 502 Bad Gateway. "
            "The API instance may be unavailable, restarting, "
            "overloaded, or failing to respond. Check the API "
            "service's Render runtime logs."
        )

    if response.status_code == 503:
        return (
            "The API is temporarily unavailable. On Render, "
            "this can happen while a free service is starting "
            "or while the service is suspended."
        )

    if response.status_code == 504:
        return (
            "The gateway timed out waiting for the API. "
            "The request may be taking too long."
        )

    if body.startswith("<") or "<html" in body.lower():
        return (
            f"HTTP {response.status_code}: the server returned "
            "an HTML error page instead of JSON."
        )

    if body:
        return body[:2000]

    return f"API request failed with HTTP {response.status_code}."


def show_request_error(error, operation):
    if isinstance(error, requests.exceptions.Timeout):
        st.error(
            f"{operation} timed out. The API may still be "
            "processing the request. Check Render logs before "
            "repeating operations that create or modify data."
        )
    elif isinstance(error, requests.exceptions.ConnectionError):
        st.error(
            f"{operation}: could not connect to the LifePass API. "
            "The backend may be sleeping, restarting, or unavailable."
        )
    else:
        st.error(f"{operation}: {error}")


def normalize_share_url(share_url):
    """Make local API share paths public without rewriting
    unrelated external URLs.
    """
    if not share_url:
        return ""

    share_url = str(share_url).strip()

    try:
        parsed = urlparse(share_url)

        if not parsed.scheme and not parsed.netloc:
            if not share_url.startswith("/"):
                return ""
            return api_url(share_url)

        if parsed.scheme not in ("http", "https"):
            return ""

        hostname = (parsed.hostname or "").lower()

        # Rewrite local development URLs only.
        if hostname in ("localhost", "127.0.0.1", "::1"):
            public = urlparse(API_URL)
            return urlunparse((
                public.scheme,
                public.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

        # Preserve legitimate public URLs.
        return share_url

    except (ValueError, TypeError):
        return ""


# =========================================================
# DOCUMENT HELPERS
# =========================================================

def get_documents():
    try:
        response = api_request(
            "GET",
            "/documents",
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
        )

        if response.status_code != 200:
            st.error(
                "Could not load documents: "
                + get_error_message(response)
            )
            return None

        data = parse_json_response(response)

        if not isinstance(data, dict):
            st.error("The documents API returned invalid JSON.")
            return None

        docs = data.get("documents", [])

        if not isinstance(docs, list):
            st.error("The API returned an invalid document list.")
            return None

        return docs

    except requests.exceptions.RequestException as e:
        show_request_error(e, "Loading documents")
        return None


def get_status_value(document):
    status = document.get("renewal_status", "unknown")

    if isinstance(status, dict):
        status = status.get("status", "unknown")

    return str(status or "unknown").lower()


def get_days_remaining(document):
    status = document.get("renewal_status")

    if isinstance(status, dict):
        return status.get("days_remaining")

    return document.get("days_remaining")


def status_label(status):
    return {
        "valid": "Valid",
        "upcoming": "Upcoming",
        "due_soon": "Due Soon",
        "critical": "Critical",
        "expired": "Expired",
        "unknown": "Unknown"
    }.get(status, "Unknown")


def status_icon(status):
    return {
        "valid": "🟢",
        "upcoming": "🔵",
        "due_soon": "🟡",
        "critical": "🟠",
        "expired": "🔴",
        "unknown": "⚪"
    }.get(status, "⚪")


def display_confidence(value):
    try:
        number = float(value)
        if 0 <= number <= 1:
            number *= 100
        return f"{number:.1f}%"
    except (TypeError, ValueError):
        return str(value if value is not None else "N/A")


def display_value(value):
    if value is None or value == "":
        return "Not detected"
    return str(value)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "upload_result": None,
    "privacy_result": None,
    "privacy_document_id": None,
    "privacy_document_name": None,
    "active_share": None,
    "download_data": {},
    "download_error": {},
    "delete_confirm": None,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =========================================================
# SIDEBAR / UPLOAD
# =========================================================

st.sidebar.title("LifePass")
st.sidebar.caption("Your documents. Your control.")
st.sidebar.divider()
st.sidebar.subheader("Upload Document")

uploaded_file = st.sidebar.file_uploader(
    "Choose a PDF, JPG or PNG",
    type=["pdf", "jpg", "jpeg", "png"],
    key="document_uploader"
)

if uploaded_file is not None:
    st.sidebar.success(f"Selected: {uploaded_file.name}")

    if st.sidebar.button(
        "Process Document",
        type="primary",
        use_container_width=True,
        key="process_document"
    ):
        progress = st.empty()

        try:
            with st.spinner(
                "Analyzing your document. OCR may take a while..."
            ):
                progress.info("Connecting to LifePass API...")

                response = api_request(
                    "POST",
                    "/predict-document",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream"
                        )
                    },
                    # Long connect/read timeout for ML processing.
                    timeout=(CONNECT_TIMEOUT, UPLOAD_TIMEOUT)
                )

            progress.empty()

            if response.status_code == 200:
                result = parse_json_response(response)

                if not isinstance(result, dict):
                    st.error("The API returned invalid JSON.")
                else:
                    st.session_state["upload_result"] = result
                    st.session_state["download_data"] = {}
                    st.session_state["download_error"] = {}
                    st.success("Document processed successfully.")
                    st.rerun()
            else:
                st.error(
                    f"Document processing failed: HTTP "
                    f"{response.status_code}"
                )
                st.code(get_error_message(response))

                if response.status_code in (502, 503, 504):
                    st.info(
                        "Check the backend logs. Do not repeatedly "
                        "submit the same document until you know "
                        "whether the first request completed."
                    )

        except requests.exceptions.RequestException as e:
            progress.empty()
            show_request_error(e, "Document processing")
        except Exception as e:
            progress.empty()
            st.error(f"Unexpected upload error: {e}")


# =========================================================
# HEADER
# =========================================================

st.title("LifePass")
st.caption("Secure Document & Renewal Management")
st.divider()


# =========================================================
# SYSTEM STATUS
# =========================================================

with st.expander("System Status"):
    st.write(f"**API URL:** `{API_URL}`")

    if not API_URL.startswith("https://"):
        st.warning(
            "The configured API URL is not HTTPS. "
            "Use HTTPS for a publicly deployed service."
        )

    if st.button("Check API", key="check_api"):
        try:
            response = api_request(
                "GET", "/", timeout=(5, 15)
            )

            if 200 <= response.status_code < 400:
                st.success(
                    f"API responded with HTTP {response.status_code}."
                )
            else:
                st.error(
                    f"API returned HTTP {response.status_code}: "
                    f"{get_error_message(response)}"
                )
        except requests.exceptions.RequestException as e:
            show_request_error(e, "API health check")


# =========================================================
# LOAD DOCUMENTS
# =========================================================

documents = get_documents()

# None means API failure; [] means the API successfully
# returned an empty list.
if documents is None:
    st.warning(
        "Document information could not be loaded. "
        "The dashboard is showing no document data until "
        "the API becomes available."
    )
    st.stop()

for document in documents:
    document["_status"] = get_status_value(document)
    document["_days_remaining"] = get_days_remaining(document)


# =========================================================
# LATEST UPLOAD RESULT
# =========================================================

result = st.session_state.get("upload_result")

if result:
    st.success(
        f"✓ {result.get('filename', 'Document')} "
        "has been processed."
    )

    with st.expander("View latest processing result"):
        c1, c2 = st.columns(2)

        with c1:
            st.write("**Document Type**")
            st.write(display_value(result.get("document_type")))

            st.write("**Expiry Date**")
            st.write(display_value(result.get("expiry_date")))

        with c2:
            st.write("**Confidence**")
            st.write(display_confidence(result.get("confidence")))

            renewal = result.get("renewal_status", {})
            if isinstance(renewal, dict):
                status = renewal.get("status", "unknown")
                days = renewal.get("days_remaining")
            else:
                status = renewal or "unknown"
                days = None

            st.write("**Renewal Status**")
            st.write(f"{status_icon(status)} {status_label(status)}")

            if days is not None:
                st.write(f"**Days Remaining:** {days}")

        fields = result.get("fields", {})
        if isinstance(fields, dict) and fields:
            st.divider()
            st.subheader("Extracted Information")
            for key, value in fields.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

        extracted_text = result.get("extracted_text", "")
        if extracted_text:
            st.text_area(
                "OCR Extracted Text",
                extracted_text,
                height=250,
                key="latest_ocr_text"
            )


# =========================================================
# OVERVIEW
# =========================================================

st.header("Overview")

total = len(documents)
counts = {
    status: sum(d.get("_status") == status for d in documents)
    for status in [
        "valid", "upcoming", "due_soon",
        "critical", "expired"
    ]
}

cols = st.columns(6)
metrics = [
    ("Documents", total),
    ("Valid", counts["valid"]),
    ("Upcoming", counts["upcoming"]),
    ("Due Soon", counts["due_soon"]),
    ("Critical", counts["critical"]),
    ("Expired", counts["expired"])
]

for col, (label, value) in zip(cols, metrics):
    with col:
        st.metric(label, value)


# =========================================================
# RENEWAL ALERTS
# =========================================================

alerts = [
    d for d in documents
    if d.get("_status") in ("expired", "critical", "due_soon")
]

if alerts:
    st.header("Renewal Alerts")

    for document in alerts:
        filename = document.get("filename", "Document")
        expiry = display_value(document.get("expiry_date"))
        status = document.get("_status")
        days = document.get("_days_remaining")

        if status == "expired":
            message = (
                f"Expired {abs(days)} days ago."
                if isinstance(days, (int, float))
                else "This document has expired."
            )
            st.error(
                f"🔴 **{filename}** — {message} "
                f"Expiry date: **{expiry}**"
            )
        elif status == "critical":
            st.warning(
                f"🟠 **{filename}** — expires in "
                f"**{days if days is not None else 'an unknown number of'} "
                f"{'days' if days is not None else ''}**. "
                f"Expiry date: **{expiry}**"
            )
        else:
            st.warning(
                f"🟡 **{filename}** — renewal due soon. "
                f"Days left: **{days if days is not None else 'N/A'}**. "
                f"Expiry date: **{expiry}**"
            )


# =========================================================
# MY DOCUMENTS / FILTERS
# =========================================================

st.header("My Documents")

search_col, type_col, status_col = st.columns([2, 1, 1])

with search_col:
    search_query = st.text_input(
        "Search documents",
        placeholder="Search by filename..."
    )

document_types = sorted({
    str(d.get("document_type") or "Unknown")
    for d in documents
})

statuses = sorted({
    d.get("_status", "unknown")
    for d in documents
})

with type_col:
    selected_type = st.selectbox(
        "Document type", ["All"] + document_types
    )

with status_col:
    selected_status = st.selectbox(
        "Status", ["All"] + statuses
    )

filtered_documents = documents

if search_query:
    filtered_documents = [
        d for d in filtered_documents
        if search_query.casefold()
        in str(d.get("filename", "")).casefold()
    ]

if selected_type != "All":
    filtered_documents = [
        d for d in filtered_documents
        if str(d.get("document_type") or "Unknown") == selected_type
    ]

if selected_status != "All":
    filtered_documents = [
        d for d in filtered_documents
        if d.get("_status") == selected_status
    ]


# =========================================================
# DOCUMENT CARDS
# =========================================================

if not filtered_documents:
    if documents:
        st.info("No documents match your search or filters.")
    else:
        st.info("You haven't uploaded any documents yet.")

for document in filtered_documents:
    document_id = document.get("id")

    if document_id is None:
        st.warning("A document without an ID was skipped.")
        continue

    document_id = str(document_id)
    filename = str(document.get("filename", "Unknown document"))
    document_type = str(document.get("document_type", "Unknown"))
    expiry = display_value(document.get("expiry_date"))
    confidence = document.get("confidence", 0)
    status = document.get("_status", "unknown")
    days = document.get("_days_remaining")

    with st.container(border=True):
        st.subheader(f"📄 {filename}")
        st.caption(f"{document_type.title()} document")

        info1, info2, info3, info4 = st.columns(4)

        with info1:
            st.caption("EXPIRY")
            st.write(f"**{expiry}**")

        with info2:
            st.caption("DAYS LEFT")
            st.write(f"**{days if days is not None else 'N/A'}**")

        with info3:
            st.caption("CONFIDENCE")
            st.write(f"**{display_confidence(confidence)}**")

        with info4:
            st.caption("STATUS")
            st.write(f"{status_icon(status)} **{status_label(status)}**")

        st.divider()

        view_col, download_col, delete_col, spacer = st.columns(
            [1, 1, 1, 5]
        )

        file_url = api_url(f"/documents/{document_id}/file")

        with view_col:
            st.link_button(
                "View",
                file_url,
                use_container_width=True
            )

        # Download cache is keyed by document ID.
        download_key = f"download_data_{document_id}"
        error_key = f"download_error_{document_id}"

        with download_col:
            if download_key not in st.session_state["download_data"]:
                if st.button(
                    "Prepare Download",
                    key=f"prepare_download_{document_id}",
                    use_container_width=True
                ):
                    try:
                        with st.spinner("Preparing document..."):
                            response = api_request(
                                "GET",
                                f"/documents/{document_id}/file",
                                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                            )

                        if response.status_code == 200:
                            st.session_state["download_data"][download_key] = {
                                "data": response.content,
                                "mime": response.headers.get(
                                    "content-type",
                                    "application/octet-stream"
                                )
                            }
                            st.session_state["download_error"].pop(
                                error_key, None
                            )
                            st.rerun()
                        else:
                            st.session_state["download_error"][error_key] = (
                                get_error_message(response)
                            )
                            st.rerun()

                    except requests.exceptions.RequestException as e:
                        st.session_state["download_error"][error_key] = str(e)
                        st.rerun()

            else:
                download_info = st.session_state["download_data"][download_key]

                st.download_button(
                    "Download File",
                    data=download_info["data"],
                    file_name=filename,
                    mime=download_info["mime"],
                    key=f"actual_download_{document_id}",
                    use_container_width=True
                )

            if error_key in st.session_state["download_error"]:
                st.error(st.session_state["download_error"][error_key])

        # Require a second confirmation before deleting.
        with delete_col:
            confirm_key = f"delete_confirm_{document_id}"

            if st.session_state.get("delete_confirm") == document_id:
                if st.button(
                    "Confirm Delete",
                    key=f"confirm_delete_{document_id}",
                    use_container_width=True
                ):
                    try:
                        response = api_request(
                            "DELETE",
                            f"/documents/{document_id}",
                            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                        )

                        if response.status_code in (200, 204):
                            st.session_state["download_data"].pop(
                                download_key, None
                            )
                            st.session_state["download_error"].pop(
                                error_key, None
                            )
                            st.session_state["delete_confirm"] = None

                            if str(st.session_state.get(
                                "privacy_document_id"
                            )) == document_id:
                                st.session_state["privacy_result"] = None
                                st.session_state["privacy_document_id"] = None
                                st.session_state["privacy_document_name"] = None
                                st.session_state["active_share"] = None

                            st.success("Document deleted.")
                            st.rerun()
                        else:
                            st.error(get_error_message(response))
                    except requests.exceptions.RequestException as e:
                        show_request_error(e, "Deleting document")

                if st.button(
                    "Cancel",
                    key=f"cancel_delete_{document_id}"
                ):
                    st.session_state["delete_confirm"] = None
                    st.rerun()
            else:
                if st.button(
                    "Delete",
                    key=f"delete_{document_id}",
                    use_container_width=True
                ):
                    st.session_state["delete_confirm"] = document_id
                    st.rerun()

        with st.expander("View document details"):
            try:
                detail_response = api_request(
                    "GET",
                    f"/documents/{document_id}",
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                )

                if detail_response.status_code == 200:
                    details = parse_json_response(detail_response)

                    if not isinstance(details, dict):
                        st.error("Invalid document details response.")
                    else:
                        d1, d2 = st.columns(2)

                        with d1:
                            for key, label in [
                                ("document_number", "Document Number"),
                                ("holder_name", "Holder Name"),
                                ("date_of_birth", "Date of Birth"),
                            ]:
                                st.write(f"**{label}**")
                                st.write(display_value(details.get(key)))

                        with d2:
                            for key, label in [
                                ("issue_date", "Issue Date"),
                                ("expiry_date", "Expiry Date"),
                            ]:
                                st.write(f"**{label}**")
                                st.write(display_value(details.get(key)))

                            st.write("**Renewal Status**")
                            st.write(
                                f"{status_icon(status)} {status_label(status)}"
                            )

                        st.divider()
                        detail_text = details.get("extracted_text", "")

                        if detail_text:
                            st.text_area(
                                "OCR Extracted Text",
                                detail_text,
                                height=250,
                                key=f"details_ocr_{document_id}"
                            )
                        else:
                            st.info("No OCR text available.")
                else:
                    st.error(get_error_message(detail_response))

            except requests.exceptions.RequestException as e:
                show_request_error(e, "Loading document details")


# =========================================================
# PRIVACY FIREWALL
# =========================================================

st.divider()
st.header("Privacy Firewall")
st.caption(
    "Review sensitive information before sharing a document."
)

if documents:
    document_options = {
        str(d["id"]): str(d.get("filename", "Unknown document"))
        for d in documents
        if d.get("id") is not None
    }

    if document_options:
        selected_document_id = st.selectbox(
            "Select a document to analyze",
            options=list(document_options.keys()),
            format_func=lambda value: document_options[value],
            key="privacy_document_selector"
        )

        if st.button(
            "Run Privacy Check",
            type="primary",
            key="run_privacy_check"
        ):
            try:
                with st.spinner("Analyzing document privacy..."):
                    detail_response = api_request(
                        "GET",
                        f"/documents/{selected_document_id}",
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                    )

                    if detail_response.status_code != 200:
                        st.error(get_error_message(detail_response))
                        st.stop()

                    details = parse_json_response(detail_response)

                    if not isinstance(details, dict):
                        st.error("Invalid document details response.")
                        st.stop()

                    fields = {
                        key: details.get(key)
                        for key in [
                            "document_number",
                            "holder_name",
                            "date_of_birth",
                            "issue_date",
                            "expiry_date",
                            "nationality"
                        ]
                        if details.get(key) not in (None, "")
                    }

                    privacy_response = api_request(
                        "POST",
                        "/privacy-check",
                        json={"fields": fields},
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                    )

                if privacy_response.status_code != 200:
                    st.error(get_error_message(privacy_response))
                else:
                    privacy_data = parse_json_response(privacy_response)

                    if not isinstance(privacy_data, dict):
                        st.error("Invalid privacy check response.")
                    else:
                        st.session_state["privacy_result"] = privacy_data
                        st.session_state["privacy_document_id"] = selected_document_id
                        st.session_state["privacy_document_name"] = (
                            document_options[selected_document_id]
                        )
                        st.session_state["active_share"] = None
                        st.rerun()

            except requests.exceptions.RequestException as e:
                show_request_error(e, "Privacy check")


# =========================================================
# PRIVACY RESULTS AND CONTROLLED SHARING
# =========================================================

privacy_result = st.session_state.get("privacy_result")

if privacy_result:
    document_name = st.session_state.get(
        "privacy_document_name", "Document"
    )
    privacy_document_id = str(
        st.session_state.get("privacy_document_id", "")
    )

    st.subheader(f"Privacy Analysis — {document_name}")

    summary = privacy_result.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric("Public", summary.get("public", 0))

    with p2:
        st.metric("Sensitive", summary.get("sensitive", 0))

    with p3:
        st.metric("Highly Sensitive", summary.get("highly_sensitive", 0))

    highly_sensitive_count = summary.get("highly_sensitive", 0)
    sensitive_count = summary.get("sensitive", 0)

    if highly_sensitive_count:
        st.error(
            f"{highly_sensitive_count} highly sensitive field(s) detected. "
            "Review carefully before sharing."
        )
    elif sensitive_count:
        st.warning(
            f"{sensitive_count} sensitive field(s) detected. "
            "Review carefully before sharing."
        )
    else:
        st.success("No sensitive fields were reported by the API.")

    privacy_fields = privacy_result.get("fields", {})

    if not isinstance(privacy_fields, dict) or not privacy_fields:
        st.info("No extractable fields were detected.")
    else:
        st.subheader("Field-Level Privacy Analysis")

        # Public fields default to selected. All sensitive fields
        # default to unselected, even if a previous run selected them.
        selected_share_fields = []

        for field_name, field_info in privacy_fields.items():
            if not isinstance(field_info, dict):
                continue

            value = field_info.get("value", "")
            level = str(
                field_info.get("level", "SENSITIVE")
            ).upper()

            readable_name = field_name.replace("_", " ").title()

            if level == "HIGHLY_SENSITIVE":
                st.error(
                    f"**{readable_name}** — Highly Sensitive"
                )
            elif level == "SENSITIVE":
                st.warning(f"**{readable_name}** — Sensitive")
            else:
                st.success(f"**{readable_name}** — Public")

            with st.expander(f"Inspect {readable_name}"):
                st.write("**Value**")
                st.write(display_value(value))
                st.write("**Privacy Level**")
                st.write(level)
                st.write(
                    "**API share_allowed value:** "
                    f"{field_info.get('share_allowed', False)}"
                )

        st.divider()
        st.subheader("Controlled Sharing")
        st.caption(
            "Only selected fields will be sent to the share endpoint. "
            "Sensitive fields are unchecked by default."
        )

        for field_name, field_info in privacy_fields.items():
            if not isinstance(field_info, dict):
                continue

            level = str(
                field_info.get("level", "SENSITIVE")
            ).upper()

            value = field_info.get("value", "")
            readable_name = field_name.replace("_", " ").title()

            default_selected = level not in (
                "SENSITIVE", "HIGHLY_SENSITIVE"
            )

            selected = st.checkbox(
                f"{readable_name} — {level.replace('_', ' ').title()}",
                value=default_selected,
                key=f"share_{privacy_document_id}_{field_name}"
            )

            if selected:
                selected_share_fields.append({
                    "field": readable_name,
                    "value": value,
                    "level": level
                })

        st.divider()
        st.subheader("Share Preview")

        if selected_share_fields:
            st.write(f"{len(selected_share_fields)} field(s) selected.")
            for item in selected_share_fields:
                st.write(f"**{item['field']}**")
                st.write(display_value(item["value"]))
                st.caption(item["level"])
        else:
            st.info("No fields selected.")

        st.divider()
        st.subheader("Secure Share Link")
        st.caption(
            "The backend must enforce expiry and restrict the link "
            "to the selected fields. Frontend selection alone is "
            "not a security boundary."
        )

        expiry_hours = st.selectbox(
            "Link expires after",
            [1, 6, 24, 72],
            index=2,
            format_func=lambda h: f"{h} hour" if h == 1 else f"{h} hours",
            key=f"share_expiry_{privacy_document_id}"
        )

        if st.button(
            "Generate Secure Share Link",
            type="primary",
            key=f"generate_share_link_{privacy_document_id}",
            disabled=not selected_share_fields
        ):
            try:
                # Do not retry this POST automatically.
                with st.spinner("Generating share link..."):
                    response = api_request(
                        "POST",
                        "/shares",
                        json={
                            "document_id": int(privacy_document_id),
                            "fields": selected_share_fields,
                            "expires_hours": int(expiry_hours)
                        },
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                    )

                if response.status_code in (200, 201):
                    share_result = parse_json_response(response)

                    if not isinstance(share_result, dict):
                        st.error("The sharing API returned invalid JSON.")
                    else:
                        share_url = normalize_share_url(
                            share_result.get("share_url", "")
                        )

                        if not share_url:
                            st.error(
                                "The API did not return a valid share URL. "
                                "Check the backend's public base URL setting."
                            )
                        else:
                            share_result["share_url"] = share_url
                            st.session_state["active_share"] = share_result
                            st.success("Share link generated.")
                            st.rerun()
                else:
                    st.error(
                        "Could not generate share link: "
                        + get_error_message(response)
                    )

                    if response.status_code in (502, 503, 504):
                        st.warning(
                            "Check the sharing API logs before trying again. "
                            "The server may have created the share even if "
                            "the response was lost."
                        )

            except requests.exceptions.RequestException as e:
                show_request_error(e, "Generating share link")

        active_share = st.session_state.get("active_share")

        if active_share:
            st.divider()
            st.subheader("Active Share")

            share_url = normalize_share_url(
                active_share.get("share_url", "")
            )

            if share_url:
                st.text_input(
                    "Share link",
                    value=share_url,
                    key=f"share_link_display_{privacy_document_id}"
                )
                st.link_button(
                    "Open Share Link",
                    share_url,
                    use_container_width=True
                )

            expires_at = active_share.get("expires_at")
            if expires_at:
                st.caption(f"Link expires at: {expires_at}")

            token = active_share.get("token")

            if token and st.button(
                "Revoke Access",
                key=f"revoke_share_{privacy_document_id}"
            ):
                try:
                    response = api_request(
                        "DELETE",
                        f"/shares/{token}",
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
                    )

                    if response.status_code in (200, 204):
                        st.session_state["active_share"] = None
                        st.success("Share access revoked.")
                        st.rerun()
                    else:
                        st.error(get_error_message(response))

                except requests.exceptions.RequestException as e:
                    show_request_error(e, "Revoking share access")


# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption("LifePass • Secure Document & Renewal Management")
