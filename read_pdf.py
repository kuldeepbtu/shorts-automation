import fitz  # PyMuPDF
import sys

def extract_pdf_text(pdf_path, output_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Extracted from {pdf_path}")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

if __name__ == "__main__":
    extract_pdf_text(r"c:\ShortsBot\Instructions\lyria.pdf", r"c:\ShortsBot\lyria.txt")
    extract_pdf_text(r"c:\ShortsBot\Instructions\lyria 2.pdf", r"c:\ShortsBot\lyria2.txt")
