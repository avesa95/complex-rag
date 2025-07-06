def build_embedding_text_from_page_metadata(metadata: dict) -> str:
    doc = metadata.get("document_metadata", {})
    section = metadata.get("section", {})
    page_number = metadata.get("page_number", "")
    content_elements = metadata.get("content_elements", [])

    # Header
    header = [
        f"Document: {doc.get('document_title', '')} ({doc.get('manufacturer', '')}, Revision {doc.get('document_revision', '')})",
        f"Section: {section.get('section_number', '')} {section.get('section_title', '')}",
        f"Subsection: {section.get('subsection_number', '')} {section.get('subsection_title', '')}",
        f"Page: {page_number}",
    ]

    # Text content
    body = []
    for el in content_elements:
        el_type = el.get("type", "")
        title = el.get("title", "")
        summary = el.get("summary", "")
        text = ""

        if el_type == "text_block":
            text += f"Text Block: {title}\nSummary: {summary}\n"
        elif el_type == "figure":
            text += f"Figure: {title} – {summary}\n"
        elif el_type == "table":
            text += f"Table: {title} – {summary}\n"

        body.append(text.strip())

    # Entities and other metadata
    all_entities = set()
    all_keywords = set()
    all_warnings = set()
    all_contexts = set()
    all_models = set()

    for el in content_elements:
        all_entities.update(el.get("entities", []))
        all_keywords.update(el.get("keywords", []))
        all_warnings.update(el.get("warnings", []))
        all_contexts.update(el.get("application_context", []))
        all_models.update(el.get("model_applicability", []))

    tail = [
        f"Entities: {', '.join(sorted(all_entities))}" if all_entities else "",
        f"Warnings: {', '.join(sorted(all_warnings))}" if all_warnings else "",
        f"Keywords: {', '.join(sorted(all_keywords))}" if all_keywords else "",
        f"Model Applicability: {', '.join(sorted(all_models))}" if all_models else "",
        f"Context: {', '.join(sorted(all_contexts))}" if all_contexts else "",
    ]

    # Final embedding text
    full_text = "\n\n".join(part for part in (header + body + tail) if part)
    return full_text


# Example: let's test with user's latest metadata input
