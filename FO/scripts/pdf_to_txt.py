import fitz  # PyMuPDF
import os

def pdf_to_txt(pdf_path, output_txt_path):
    doc = fitz.open(pdf_path)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for page in doc:
            f.write(page.get_text())

# Ejemplo de uso:
pdf_to_txt("data/oposiciones.pdf", "documents/oposiciones.txt")
