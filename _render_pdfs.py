import fitz
from pathlib import Path

out_dir = Path(r"c:\ShortsBot\Instructions\images")
out_dir.mkdir(exist_ok=True)

for fname in ["gemini.pdf", "text.pdf"]:
    doc = fitz.open(rf"c:\ShortsBot\Instructions\{fname}")
    prefix = fname.replace(".pdf", "")
    for pnum, page in enumerate(doc):
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        total_h = pix.height
        chunk_h = 3000  # pixels per chunk
        chunk_num = 0
        for y in range(0, total_h, chunk_h):
            clip = fitz.Rect(0, y/2.0, page.rect.width, min((y+chunk_h)/2.0, page.rect.height))
            pix_chunk = page.get_pixmap(matrix=mat, clip=clip)
            out_path = out_dir / f"{prefix}_p{pnum}_chunk{chunk_num}.png"
            pix_chunk.save(str(out_path))
            print(f"Saved: {out_path.name} ({pix_chunk.width}x{pix_chunk.height})")
            chunk_num += 1
