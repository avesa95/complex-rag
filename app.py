import os

import streamlit as st

from retrieval import ManufacturingRetrieval

try:
    from streamlit_pdf_viewer import pdf_viewer
except ImportError:
    st.error("Please install streamlit-pdf-viewer: pip install streamlit-pdf-viewer")
    st.stop()

st.set_page_config(layout="wide")
st.title("Service Manual Q&A with PDF Viewer and References")

# --- PDF Upload or Default ---
st.sidebar.header("PDF Document")
pdf_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])
pdf_path = None

if pdf_file:
    pdf_path = f"uploaded_{pdf_file.name}"
    with open(pdf_path, "wb") as f:
        f.write(pdf_file.read())
    st.sidebar.success(f"PDF uploaded: {pdf_file.name}")
else:
    # Use your default PDF (already indexed)
    pdf_path = "data/service_manual_long.pdf"
    st.sidebar.info("Using default PDF (already indexed)")

# --- Session state for PDF page ---
if "pdf_page" not in st.session_state:
    st.session_state["pdf_page"] = 1


def show_pdf():
    if os.path.exists(pdf_path):
        pdf_viewer(pdf_path, height=900)
    else:
        st.warning("PDF file not found.")


# --- Layout: Two columns, PDF left, chat right ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### PDF Viewer")
    if os.path.exists(pdf_path):
        pdf_viewer(pdf_path, height=900)
    else:
        st.warning("PDF file not found.")

with col_right:
    st.markdown("### Ask a question about the service manual")
    user_question = st.text_area("Your question:", height=80)
    submit = st.button("Get Answer")

    if submit and user_question.strip():
        with st.spinner("Retrieving answer..."):
            retrieval = ManufacturingRetrieval()
            relevant_points = retrieval.retrieve_relevant_points(user_question)
            result = retrieval.answer_question(relevant_points, user_question)
            answer = result["answer"]
            references = result["references"]

        st.markdown("## Answer")
        st.markdown(answer)

        st.markdown("---")
        st.markdown("## References")

        def show_reference(ref, ref_type):
            page = ref["page_number"]
            subq = ref["sub_question"]
            st.write(f"**Sub-question:** {subq} | **Page:** {page}")
            if ref_type == "table":
                if "png_file" in ref and os.path.exists(ref["png_file"]):
                    st.image(
                        ref["png_file"],
                        caption=ref["element_id"],
                        use_column_width=True,
                    )
            elif ref_type == "figure":
                if "png_file" in ref and os.path.exists(ref["png_file"]):
                    st.image(
                        ref["png_file"], caption=ref["label"], use_column_width=True
                    )

        if references["tables"]:
            st.markdown("### Tables")
            for table in references["tables"]:
                show_reference(table, "table")
        else:
            st.write("No tables referenced.")

        if references["figures"]:
            st.markdown("### Figures")
            for figure in references["figures"]:
                show_reference(figure, "figure")
        else:
            st.write("No figures referenced.")

    else:
        st.info("Enter a question and press 'Get Answer'.")

st.markdown("---")
st.caption("Demo: Service Manual Q&A with Table and Figure References + PDF Viewer")
