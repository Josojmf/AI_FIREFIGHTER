from fpdf import FPDF
import json

def generar_pdf(input_json, output_pdf):
    with open(input_json, encoding="utf-8") as f:
        preguntas = json.load(f)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for i, q in enumerate(preguntas, start=1):
        pdf.multi_cell(0, 10, f"{i}. {q['pregunta']}")
        for idx, opcion in enumerate(q['opciones'], start=65):  # 65 = A
            pdf.cell(0, 10, f"   {chr(idx)}. {opcion}", ln=True)
        pdf.ln(5)

    pdf.output(output_pdf)

# Ejemplo:
generar_pdf("data/questions.json", "cuestionario_bomberos.pdf")
