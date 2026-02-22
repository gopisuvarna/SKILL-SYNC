import fitz  # PyMuPDF


def extract_text_from_pdf(file):
    """
    Extract full text from uploaded PDF file
    """
    text = ""

    # Open PDF from uploaded file stream
    pdf = fitz.open(stream=file.read(), filetype="pdf")

    # Loop through all pages
    for page in pdf:
        text += page.get_text()

    pdf.close()
    return text
