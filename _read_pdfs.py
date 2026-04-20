import fitz

pdfs = [
    (r"c:\ShortsBot\Instructions\gemini.pdf", r"c:\ShortsBot\Instructions\gemini.txt"),
    (r"c:\ShortsBot\Instructions\text.pdf",   r"c:\ShortsBot\Instructions\text.txt"),
]

for pdf_path, out_path in pdfs:
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"OK: {pdf_path} -> {len(text)} chars, {len(doc)} pages")
    except Exception as e:
        print(f"ERROR {pdf_path}: {e}")
