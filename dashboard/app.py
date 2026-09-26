import streamlit as st
import requests
import os

# =========================================================
# CONFIGURATION
# =========================================================

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)


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
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       MAIN APPLICATION
       ===================================================== */

    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }


    /* =====================================================
       TEXT FONT
       IMPORTANT:
       Do NOT use .stApp * because that breaks
       Streamlit's internal icon fonts.
       ===================================================== */

    .stApp p,
    .stApp label,
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6,
    .stApp button,
    .stApp input,
    .stApp textarea {

        font-family:
            "Trebuchet MS",
            "Segoe UI",
            Arial,
            sans-serif;

    }


    /* =====================================================
       MAIN TITLE
       ===================================================== */

    .stApp h1 {

        font-size: 48px !important;

        font-weight: 800 !important;

        letter-spacing: -1px;

        color: #172033 !important;

        line-height: 1.2 !important;

        margin-bottom: 0.5rem !important;

    }


    /* =====================================================
       SECTION HEADINGS
       ===================================================== */

    .stApp h2 {

        font-size: 30px !important;

        font-weight: 750 !important;

        color: #172033 !important;

        line-height: 1.3 !important;

    }


    .stApp h3 {

        font-size: 21px !important;

        font-weight: 700 !important;

        color: #172033 !important;

        line-height: 1.4 !important;

    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    section[data-testid="stSidebar"] {

        background-color: #172033;

    }


    section[data-testid="stSidebar"] p {

        color: #d1d5db !important;

    }


    section[data-testid="stSidebar"] label {

        color: #ffffff !important;

    }


    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {

        color: #ffffff !important;

    }


    /* Sidebar LifePass title */

    section[data-testid="stSidebar"] h1 {

        font-size: 38px !important;

        font-weight: 800 !important;

        line-height: 1.2 !important;

    }


    /* =====================================================
       FILE UPLOADER
       ===================================================== */

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] {

        background-color: #ffffff !important;

        border: 1px solid #d1d5db !important;

        border-radius: 12px !important;

    }


    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] p {

        color: #172033 !important;

        font-family:
            "Trebuchet MS",
            "Segoe UI",
            Arial,
            sans-serif !important;

    }


    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] span {

        color: #172033 !important;

    }


    /* Upload button */

    section[data-testid="stSidebar"]
    [data-testid="stFileUploaderDropzone"] button {

        background-color: #f3f4f6 !important;

        color: #172033 !important;

        border: 1px solid #d1d5db !important;

        border-radius: 8px !important;

    }


    /* =====================================================
       SIDEBAR PROCESS BUTTON
       ===================================================== */

    section[data-testid="stSidebar"]
    .stButton > button {

        background-color: #ffffff !important;

        color: #172033 !important;

        border-radius: 9px !important;

        font-weight: 700 !important;

    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    div[data-testid="stMetric"] {

        background-color: #ffffff;

        border: 1px solid #e5e7eb;

        border-radius: 15px;

        padding: 17px;

        box-shadow:
            0 3px 12px
            rgba(0, 0, 0, 0.05);

    }


    div[data-testid="stMetric"] label {

        color: #6b7280 !important;

    }


    div[data-testid="stMetric"]
    [data-testid="stMetricValue"] {

        color: #172033 !important;

        font-size: 28px;

        font-weight: 800;

    }


    /* =====================================================
       DOCUMENT CARDS
       ===================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {

        background-color: #ffffff;

        border-radius: 16px;

        border: 1px solid #e5e7eb;

        box-shadow:
            0 4px 15px
            rgba(0, 0, 0, 0.04);

    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    .stButton > button {

        border-radius: 9px !important;

        font-weight: 600 !important;

        min-height: 40px !important;

    }


    .stDownloadButton > button {

        border-radius: 9px !important;

        font-weight: 600 !important;

        min-height: 40px !important;

    }


    /* =====================================================
       EXPANDERS
       ===================================================== */

    div[data-testid="stExpander"] {

        background-color: #ffffff;

        border-radius: 10px;

        border: 1px solid #d1d5db;

    }


    /* =====================================================
       TEXT AREA
       ===================================================== */

    textarea {

        color: #172033 !important;

        background-color: #ffffff !important;

    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_documents():

    try:

        response = requests.get(
            f"{API_URL}/documents",
            timeout=10
        )

        if response.status_code == 200:

            return response.json().get(
                "documents",
                []
            )

        return []

    except Exception as e:

        st.warning(
            f"Could not connect to API: {e}"
        )

        return []


def status_label(status):

    labels = {

        "valid": "Valid",

        "upcoming": "Upcoming",

        "due_soon": "Due Soon",

        "critical": "Critical",

        "expired": "Expired",

        "unknown": "Unknown"

    }

    return labels.get(
        status,
        "Unknown"
    )


def status_icon(status):

    icons = {

        "valid": "🟢",

        "upcoming": "🔵",

        "due_soon": "🟡",

        "critical": "🟠",

        "expired": "🔴",

        "unknown": "⚪"

    }

    return icons.get(
        status,
        "⚪"
    )


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("LifePass")

st.sidebar.caption(
    "Your documents. Your control."
)

st.sidebar.divider()

st.sidebar.subheader(
    "Upload Document"
)


uploaded_file = st.sidebar.file_uploader(

    "Choose a PDF, JPG or PNG",

    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png"
    ]
)


if uploaded_file is not None:

    st.sidebar.success(
        f"Selected: {uploaded_file.name}"
    )

    process_button = st.sidebar.button(

        "Process Document",

        type="primary",

        use_container_width=True
    )


    if process_button:

        files = {

            "file": (

                uploaded_file.name,

                uploaded_file.getvalue(),

                uploaded_file.type
            )
        }


        try:

            with st.spinner(
                "Analyzing your document..."
            ):

                response = requests.post(

                    f"{API_URL}/predict-document",

                    files=files,

                    timeout=120
                )


            if response.status_code == 200:

                st.session_state[
                    "upload_result"
                ] = response.json()

                st.sidebar.success(
                    "Document processed successfully!"
                )

                st.rerun()


            else:

                st.sidebar.error(
                    response.text
                )


        except Exception as e:

            st.sidebar.error(
                f"Could not connect to API: {e}"
            )


# =========================================================
# MAIN HEADER
# =========================================================

st.title("LifePass")

st.caption(
    "Secure Document & Renewal Management"
)

st.divider()


# =========================================================
# LOAD DOCUMENTS
# =========================================================

documents = get_documents()


# =========================================================
# LATEST UPLOAD RESULT
# =========================================================

if "upload_result" in st.session_state:

    result = st.session_state[
        "upload_result"
    ]

    st.success(
        f"✓ {result.get('filename', 'Document')} "
        "has been processed and saved."
    )

    with st.expander(
        "View latest processing result"
    ):

        result_col1, result_col2 = st.columns(2)

        with result_col1:

            st.write(
                f"**Document Type:** "
                f"{result.get('document_type', 'Unknown')}"
            )

            st.write(
                f"**Expiry Date:** "
                f"{result.get('expiry_date', 'Not detected')}"
            )

        with result_col2:

            confidence = result.get(
                "confidence",
                0
            )

            st.write(
                f"**Confidence:** "
                f"{confidence * 100:.1f}%"
            )

            renewal = result.get(
                "renewal_status",
                {}
            )

            st.write(
                f"**Status:** "
                f"{status_label(renewal.get('status'))}"
            )


# =========================================================
# OVERVIEW
# =========================================================

st.header("Overview")


total = len(documents)


valid = sum(
    d.get("renewal_status") == "valid"
    for d in documents
)


upcoming = sum(
    d.get("renewal_status") == "upcoming"
    for d in documents
)


due_soon = sum(
    d.get("renewal_status") == "due_soon"
    for d in documents
)


critical = sum(
    d.get("renewal_status") == "critical"
    for d in documents
)


expired = sum(
    d.get("renewal_status") == "expired"
    for d in documents
)


col1, col2, col3, col4, col5, col6 = st.columns(6)


with col1:

    st.metric(
        "Documents",
        total
    )


with col2:

    st.metric(
        "Valid",
        valid
    )


with col3:

    st.metric(
        "Upcoming",
        upcoming
    )


with col4:

    st.metric(
        "Due Soon",
        due_soon
    )


with col5:

    st.metric(
        "Critical",
        critical
    )


with col6:

    st.metric(
        "Expired",
        expired
    )


# =========================================================
# RENEWAL ALERTS
# =========================================================

alerts = [

    document

    for document in documents

    if document.get("renewal_status")

    in [
        "expired",
        "critical",
        "due_soon"
    ]
]


if alerts:

    st.header("Renewal Alerts")

    for document in alerts:

        filename = document.get(
            "filename",
            "Document"
        )

        expiry = document.get(
            "expiry_date"
        ) or "Not detected"

        status = document.get(
            "renewal_status",
            "unknown"
        )

        days = document.get(
            "days_remaining"
        )


        if status == "expired":

            st.error(

                f"🔴 **Document Expired**\n\n"
                f"**{filename}** expired "
                f"{abs(days)} days ago.\n\n"
                f"Expiry date: **{expiry}**"
            )


        elif status == "critical":

            st.warning(

                f"🟠 **Renewal Required Soon**\n\n"
                f"**{filename}** expires "
                f"in **{days} days**.\n\n"
                f"Expiry date: **{expiry}**"
            )


        else:

            st.warning(

                f"🟡 **Renewal Due Soon**\n\n"
                f"**{filename}** expires "
                f"in **{days} days**.\n\n"
                f"Expiry date: **{expiry}**"
            )


# =========================================================
# MY DOCUMENTS
# =========================================================

st.header("My Documents")


# =========================================================
# SEARCH AND FILTERS
# =========================================================

search_col, type_col, status_col = st.columns(
    [2, 1, 1]
)


with search_col:

    search_query = st.text_input(

        "Search documents",

        placeholder="Search by filename..."

    )


with type_col:

    document_types = sorted(

        set(

            d.get(
                "document_type",
                "Unknown"
            )

            for d in documents

        )

    )

    selected_type = st.selectbox(

        "Document type",

        ["All"] + document_types

    )


with status_col:

    statuses = sorted(

        set(

            d.get(
                "renewal_status",
                "unknown"
            )

            for d in documents

        )

    )

    selected_status = st.selectbox(

        "Status",

        ["All"] + statuses

    )


# =========================================================
# FILTER DOCUMENTS
# =========================================================

filtered_documents = documents


if search_query:

    filtered_documents = [

        d

        for d in filtered_documents

        if search_query.lower()

        in d.get(
            "filename",
            ""
        ).lower()

    ]


if selected_type != "All":

    filtered_documents = [

        d

        for d in filtered_documents

        if d.get(
            "document_type"
        ) == selected_type

    ]


if selected_status != "All":

    filtered_documents = [

        d

        for d in filtered_documents

        if d.get(
            "renewal_status"
        ) == selected_status

    ]


# =========================================================
# NO DOCUMENTS
# =========================================================

if not filtered_documents:

    if documents:

        st.info(
            "No documents match your search or filters."
        )

    else:

        st.info(
            "You haven't uploaded any documents yet."
        )


# =========================================================
# DOCUMENT CARDS
# =========================================================

else:

    for document in filtered_documents:

        document_id = document.get(
            "id"
        )

        filename = document.get(
            "filename",
            "Unknown document"
        )

        document_type = document.get(
            "document_type",
            "Unknown"
        )

        confidence = document.get(
            "confidence",
            0
        )

        expiry = document.get(
            "expiry_date"
        ) or "Not detected"

        status = document.get(
            "renewal_status",
            "unknown"
        )

        days = document.get(
            "days_remaining"
        )

        file_path = document.get(
            "file_path"
        )


        # =========================================
        # DOCUMENT CARD
        # =========================================

        with st.container(border=True):

            st.subheader(
                f"📄 {filename}"
            )

            st.caption(
                f"{document_type.title()} document"
            )


            info1, info2, info3, info4 = st.columns(4)


            with info1:

                st.caption(
                    "EXPIRY"
                )

                st.write(
                    f"**{expiry}**"
                )


            with info2:

                st.caption(
                    "DAYS LEFT"
                )

                st.write(
                    f"**{days if days is not None else 'N/A'}**"
                )

                


            with info3:

                st.caption(
                    "CONFIDENCE"
                )

                st.write(
                    f"**{confidence * 100:.1f}%**"
                )


            with info4:

                st.caption(
                    "STATUS"
                )

                st.write(

                    f"{status_icon(status)} "
                    f"**{status_label(status)}**"

                )


            st.divider()


            # =====================================
            # ACTION BUTTONS
            # =====================================

            view_col, download_col, delete_col, spacer = st.columns(
                [1, 1, 1, 5]
            )


            file_url = (

                f"{API_URL}"
                f"/documents/"
                f"{document_id}"
                f"/file"

            )


            # =====================================
            # VIEW
            # =====================================

            with view_col:

                if file_path:

                    st.link_button(

                        "View",

                        file_url,

                        use_container_width=True

                    )

                else:

                    st.button(

                        "View",

                        disabled=True,

                        key=(
                            f"view_"
                            f"{document_id}"
                        ),

                        use_container_width=True

                    )


            # =====================================
            # DOWNLOAD
            # =====================================

            with download_col:

                if file_path:

                    try:

                        file_response = requests.get(

                            file_url,

                            timeout=20

                        )


                        if (

                            file_response.status_code

                            == 200

                        ):

                            st.download_button(

                                "Download",

                                data=file_response.content,

                                file_name=filename,

                                mime=file_response.headers.get(

                                    "content-type",

                                    "application/octet-stream"

                                ),

                                key=(

                                    f"download_"
                                    f"{document_id}"

                                ),

                                use_container_width=True

                            )

                        else:

                            st.button(

                                "Download",

                                disabled=True,

                                key=(

                                    f"download_error_"
                                    f"{document_id}"

                                ),

                                use_container_width=True

                            )


                    except Exception:

                        st.button(

                            "Download",

                            disabled=True,

                            key=(

                                f"download_exception_"
                                f"{document_id}"

                            ),

                            use_container_width=True

                        )

                else:

                    st.button(

                        "Download",

                        disabled=True,

                        key=(

                            f"download_old_"
                            f"{document_id}"

                        ),

                        use_container_width=True

                    )


            # =====================================
            # DELETE
            # =====================================

            with delete_col:

                delete_button = st.button(

                    "Delete",

                    key=(

                        f"delete_"
                        f"{document_id}"

                    ),

                    use_container_width=True

                )


                if delete_button:

                    try:

                        delete_response = requests.delete(

                            f"{API_URL}"
                            f"/documents/"
                            f"{document_id}",

                            timeout=20

                        )


                        if (

                            delete_response.status_code

                            == 200

                        ):

                            st.success(
                                "Document deleted."
                            )

                            st.rerun()


                        else:

                            st.error(
                                delete_response.text
                            )


                    except Exception as e:

                        st.error(
                            f"Delete failed: {e}"
                        )


            # =====================================
            # DOCUMENT DETAILS
            # =====================================

            with st.expander(
                "View document details"
            ):

                try:

                    detail_response = requests.get(

                        f"{API_URL}"
                        f"/documents/"
                        f"{document_id}",

                        timeout=10

                    )


                    if (

                        detail_response.status_code

                        == 200

                    ):

                        details = (
                            detail_response.json()
                        )


                        # =================================
                        # EXTRACTED INFORMATION
                        # =================================

                        st.subheader(
                            "Extracted Information"
                        )


                        detail_col1, detail_col2 = st.columns(2)


                        with detail_col1:

                            st.write(
                                "**Document Number**"
                            )

                            st.write(

                                details.get(
                                    "document_number"
                                )

                                or

                                "Not detected"

                            )


                            st.write(
                                "**Holder Name**"
                            )

                            st.write(

                                details.get(
                                    "holder_name"
                                )

                                or

                                "Not detected"

                            )


                            st.write(
                                "**Date of Birth**"
                            )

                            st.write(

                                details.get(
                                    "date_of_birth"
                                )

                                or

                                "Not detected"

                            )


                        with detail_col2:

                            st.write(
                                "**Issue Date**"
                            )

                            st.write(

                                details.get(
                                    "issue_date"
                                )

                                or

                                "Not detected"

                            )


                            st.write(
                                "**Expiry Date**"
                            )

                            st.write(

                                details.get(
                                    "expiry_date"
                                )

                                or

                                "Not detected"

                            )


                            st.write(
                                "**Renewal Status**"
                            )

                            st.write(

                                f"{status_icon(status)} "
                                f"{status_label(status)}"

                            )


                        # =================================
                        # OCR TEXT
                        # =================================

                        st.divider()


                        st.subheader(
                            "OCR Extracted Text"
                        )


                        detail_text = details.get(
                            "extracted_text",
                            ""
                        )


                        if detail_text:

                            st.text_area(

                                "Document text",

                                detail_text,

                                height=250,

                                key=(

                                    f"details_ocr_"
                                    f"{document_id}"

                                )

                            )

                        else:

                            st.info(
                                "No OCR text available."
                            )


                    else:

                        st.error(
                            "Could not load document details."
                        )


                except Exception as e:

                    st.error(
                        f"Could not load details: {e}"
                    )


# =========================================================
# FOOTER
# =========================================================

# ==========================================
# PRIVACY FIREWALL
# ==========================================

st.divider()

st.header("Privacy Firewall")

st.caption(
    "Check what sensitive information your document contains "
    "before sharing it."
)

if documents:

    document_options = {
        document.get("id"): document.get(
            "filename", "Unknown document"
        )
        for document in documents
    }

    selected_document_id = st.selectbox(
        "Select a document to analyze",
        options=list(document_options.keys()),
        format_func=lambda x: document_options[x],
        key="privacy_document_selector"
    )

    if st.button(
        "Run Privacy Check",
        type="primary",
        use_container_width=False,
        key="run_privacy_check"
    ):

        try:

            detail_response = requests.get(
                f"{API_URL}/documents/{selected_document_id}",
                timeout=10
            )

            if detail_response.status_code != 200:

                st.error(
                    "Could not load document details."
                )

            else:

                details = detail_response.json()

                fields = {
                    "document_number": details.get(
                        "document_number"
                    ),
                    "holder_name": details.get(
                        "holder_name"
                    ),
                    "date_of_birth": details.get(
                        "date_of_birth"
                    ),
                    "issue_date": details.get(
                        "issue_date"
                    ),
                    "expiry_date": details.get(
                        "expiry_date"
                    ),
                    "nationality": details.get(
                        "nationality"
                    )
                }

                fields = {
                    key: value
                    for key, value in fields.items()
                    if value
                }

                privacy_response = requests.post(
                    f"{API_URL}/privacy-check",
                    json={"fields": fields},
                    timeout=10
                )

                if privacy_response.status_code != 200:

                    st.error(
                        "Privacy analysis failed."
                    )

                else:

                    st.session_state[
                        "privacy_result"
                    ] = privacy_response.json()

                    st.session_state[
                        "privacy_document_id"
                    ] = selected_document_id

                    st.session_state[
                        "privacy_document_name"
                    ] = document_options[
                        selected_document_id
                    ]

                    # Clear an older generated share whenever
                    # a new privacy check is performed.
                    st.session_state.pop(
                        "secure_share_data",
                        None
                    )

                    st.session_state.pop(
                        "active_share",
                        None
                    )

                    st.rerun()

        except Exception as e:

            st.error(
                f"Privacy check failed: {e}"
            )


# ==========================================
# DISPLAY PRIVACY RESULT
# ==========================================

if "privacy_result" in st.session_state:

    result = st.session_state[
        "privacy_result"
    ]

    document_name = st.session_state.get(
        "privacy_document_name",
        "Document"
    )

    privacy_document_id = st.session_state.get(
        "privacy_document_id",
        "unknown"
    )

    st.subheader(
        f"Privacy Analysis — {document_name}"
    )

    summary = result.get(
        "summary",
        {}
    )

    public_count = summary.get(
        "public",
        0
    )

    sensitive_count = summary.get(
        "sensitive",
        0
    )

    highly_sensitive_count = summary.get(
        "highly_sensitive",
        0
    )

    # ------------------------------------------
    # Summary metrics
    # ------------------------------------------

    privacy_col1, privacy_col2, privacy_col3 = st.columns(3)

    with privacy_col1:

        st.metric(
            "Public",
            public_count
        )

    with privacy_col2:

        st.metric(
            "Sensitive",
            sensitive_count
        )

    with privacy_col3:

        st.metric(
            "Highly Sensitive",
            highly_sensitive_count
        )

    st.divider()

    # ------------------------------------------
    # Privacy warning
    # ------------------------------------------

    if highly_sensitive_count > 0:

        st.error(
            f"⚠️ This document contains "
            f"{highly_sensitive_count} highly sensitive field(s). "
            "Review them before sharing."
        )

    elif sensitive_count > 0:

        st.warning(
            f"⚠️ This document contains "
            f"{sensitive_count} sensitive field(s). "
            "Review the information before sharing."
        )

    else:

        st.success(
            "No sensitive information was detected."
        )

    # ------------------------------------------
    # Field-level analysis
    # ------------------------------------------

    st.subheader("Field-Level Privacy Analysis")

    privacy_fields = result.get(
        "fields",
        {}
    )

    if privacy_fields:

        for field_name, field_info in privacy_fields.items():

            value = field_info.get(
                "value",
                ""
            )

            level = field_info.get(
                "level",
                "UNKNOWN"
            )

            share_allowed = field_info.get(
                "share_allowed",
                False
            )

            readable_name = (
                field_name
                .replace("_", " ")
                .title()
            )

            if level == "HIGHLY_SENSITIVE":

                st.error(
                    f"🔴 **{readable_name}**  \n"
                    f"Value: `{value}`  \n"
                    f"Privacy Level: **Highly Sensitive**  \n"
                    f"Share by default: **No**"
                )

            elif level == "SENSITIVE":

                st.warning(
                    f"🟠 **{readable_name}**  \n"
                    f"Value: `{value}`  \n"
                    f"Privacy Level: **Sensitive**  \n"
                    f"Share by default: **No**"
                )

            else:

                st.success(
                    f"🟢 **{readable_name}**  \n"
                    f"Value: `{value}`  \n"
                    f"Privacy Level: **Public**  \n"
                    f"Share by default: "
                    f"**{'Yes' if share_allowed else 'No'}**"
                )

        # ==========================================
        # CONTROLLED SHARING
        # ==========================================

        st.divider()

        st.subheader("Controlled Sharing")

        st.caption(
            "Choose exactly which fields you want to share. "
            "Sensitive information is disabled by default."
        )

        selected_share_fields = []

        for field_name, field_info in privacy_fields.items():

            value = field_info.get(
                "value",
                ""
            )

            level = field_info.get(
                "level",
                "SENSITIVE"
            )

            readable_name = (
                field_name
                .replace("_", " ")
                .title()
            )

            checkbox_key = (
                f"share_"
                f"{privacy_document_id}_"
                f"{field_name}"
            )

            if level == "HIGHLY_SENSITIVE":

                share = st.checkbox(
                    f"🔴 {readable_name} — Highly Sensitive",
                    value=False,
                    key=checkbox_key
                )

                st.caption(
                    "Highly sensitive information. "
                    "Disabled by default."
                )

            elif level == "SENSITIVE":

                share = st.checkbox(
                    f"🟠 {readable_name} — Sensitive",
                    value=False,
                    key=checkbox_key
                )

                st.caption(
                    "Sensitive information. "
                    "Review before sharing."
                )

            else:

                share = st.checkbox(
                    f"🟢 {readable_name} — Public",
                    value=True,
                    key=checkbox_key
                )

                st.caption(
                    "Low-sensitivity information."
                )

            if share:

                selected_share_fields.append({
                    "field": readable_name,
                    "value": value,
                    "level": level
                })

        # ==========================================
        # SHARE PREVIEW
        # ==========================================

        st.divider()

        st.subheader("Share Preview")

        if selected_share_fields:

            st.success(
                f"{len(selected_share_fields)} field(s) "
                "selected for sharing."
            )

            for item in selected_share_fields:

                st.markdown(
                    f"**{item['field']}**  \n"
                    f"Value: `{item['value']}`  \n"
                    f"Privacy Level: **{item['level']}**"
                )

            if st.button(
                "Generate Secure Share",
                type="primary",
                key="generate_secure_share",
                use_container_width=False
            ):

                st.session_state[
                    "secure_share_data"
                ] = selected_share_fields

                st.success(
                    "Secure share package generated."
                )

        else:

            st.info(
                "No fields selected. "
                "Select the information you want to share."
            )

        # ==========================================
        # SECURE SHARE LINK
        # ==========================================

        st.divider()

        st.subheader("Secure Share Link")

        st.caption(
            "Generate a temporary link containing only the fields you selected above."
        )

        expiry_hours = st.selectbox(
            "Link expires after",
            [1, 6, 24, 72],
            index=2,
            format_func=lambda hours: (
                f"{hours} hour" if hours == 1 else f"{hours} hours"
            ),
            key=f"share_expiry_{privacy_document_id}"
        )

        generate_share = st.button(
            "Generate Secure Share Link",
            type="primary",
            key=f"generate_share_link_{privacy_document_id}",
            use_container_width=False,
            disabled=not selected_share_fields
        )

        if generate_share:

            try:

                share_response = requests.post(
                    f"{API_URL}/shares",
                    json={
                        "document_id": int(privacy_document_id),
                        "fields": selected_share_fields,
                        "expires_hours": int(expiry_hours)
                    },
                    timeout=15
                )

                if share_response.status_code == 200:

                    share_result = share_response.json()

                    st.session_state[
                        "active_share"
                    ] = share_result

                    st.success(
                        "Secure share link generated successfully."
                    )

                else:

                    st.error(
                        f"Could not generate share link: "
                        f"{share_response.text}"
                    )

            except Exception as e:

                st.error(
                    f"Could not connect to the sharing service: {e}"
                )

        # ------------------------------------------
        # DISPLAY ACTIVE SHARE
        # ------------------------------------------

        active_share = st.session_state.get(
            "active_share"
        )

        if active_share:

            st.success(
                "Only the selected fields are available through this link."
            )

            share_url = active_share.get(
                "share_url",
                ""
            )

            expires_at = active_share.get(
                "expires_at",
                ""
            )

            st.text_input(
                "Share link",
                value=share_url,
                key="share_link_display"
            )

            st.caption(
                f"Link expires at: {expires_at}"
            )

            link_col1, link_col2 = st.columns(2)

            with link_col1:

                if share_url:

                    st.link_button(
                        "Open Share Link",
                        share_url,
                        use_container_width=True
                    )

            with link_col2:

                revoke_share = st.button(
                    "Revoke Access",
                    key="revoke_share_link",
                    use_container_width=True
                )

                if revoke_share:

                    token = active_share.get(
                        "token"
                    )

                    try:

                        revoke_response = requests.delete(
                            f"{API_URL}/shares/{token}",
                            timeout=10
                        )

                        if revoke_response.status_code == 200:

                            st.session_state.pop(
                                "active_share",
                                None
                            )

                            st.success(
                                "Share access has been revoked."
                            )

                            st.rerun()

                        else:

                            st.error(
                                f"Could not revoke access: "
                                f"{revoke_response.text}"
                            )

                    except Exception as e:

                        st.error(
                            f"Could not connect to the sharing service: {e}"
                        )

        st.caption(
            "LifePass Privacy Firewall ensures that unselected fields are never included in the share package."
        )

    else:

        st.info(
            "No extractable fields were detected for this document."
        )

elif not documents:

    st.info(
        "Upload a document first to use the Privacy Firewall."
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "LifePass • Secure Document & Renewal Management"
)
