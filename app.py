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
        st.markdown("## 📚 References")

        # Group references by sub-question
        def group_references_by_subquestion(references):
            grouped = {}
            for ref_type in ["tables", "figures"]:
                for ref in references[ref_type]:
                    subq = ref.get("sub_question", "General")
                    if subq not in grouped:
                        grouped[subq] = {"tables": [], "figures": []}
                    grouped[subq][ref_type].append(ref)
            return grouped

        grouped_refs = group_references_by_subquestion(references)

        # Display grouped references
        for subq, refs in grouped_refs.items():
            total_refs = len(refs["tables"]) + len(refs["figures"])
            if total_refs == 0:
                continue

            with st.expander(f"🔍 {subq} ({total_refs} references)", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    if refs["tables"]:
                        st.markdown("**📊 Tables**")
                        for i, table in enumerate(refs["tables"], 1):
                            with st.container():
                                st.markdown(
                                    f"**Table {i}** - Page {table.get('page_number', 'N/A')}"
                                )
                                st.markdown(f"*ID: {table.get('element_id', 'N/A')}*")

                                # Show table image if available
                                if "png_file" in table and os.path.exists(
                                    table["png_file"]
                                ):
                                    with st.expander("📷 View Table", expanded=False):
                                        st.image(
                                            table["png_file"],
                                            caption=f"Table: {table.get('element_id', 'N/A')}",
                                            use_column_width=True,
                                        )
                                st.markdown("---")

                with col2:
                    if refs["figures"]:
                        st.markdown("**🖼️ Figures**")
                        for i, figure in enumerate(refs["figures"], 1):
                            with st.container():
                                st.markdown(
                                    f"**Figure {i}** - Page {figure.get('page_number', 'N/A')}"
                                )
                                st.markdown(f"*Label: {figure.get('label', 'N/A')}*")

                                # Show figure image if available
                                if "png_file" in figure and os.path.exists(
                                    figure["png_file"]
                                ):
                                    with st.expander("📷 View Figure", expanded=False):
                                        st.image(
                                            figure["png_file"],
                                            caption=f"Figure: {figure.get('label', 'N/A')}",
                                            use_column_width=True,
                                        )
                                st.markdown("---")

        # Show summary if no references found
        if not any(references.values()):
            st.info("No specific tables or figures referenced in this answer.")

    else:
        st.info("Enter a question and press 'Get Answer'.")

st.markdown("---")
st.caption("Demo: Service Manual Q&A with Table and Figure References + PDF Viewer")
