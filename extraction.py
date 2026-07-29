def extract_text_from_file(file_obj):
    # Determine file extension
    file_name = file_obj.name if hasattr(file_obj, "name") else file_obj
    if file_name.lower().endswith('.pdf'):
        from PyPDF2 import PdfReader
        reader = PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    elif file_name.lower().endswith('.docx'):
        import docx
        doc = docx.Document(file_obj)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    else:
        raise ValueError("Unsupported file type")
