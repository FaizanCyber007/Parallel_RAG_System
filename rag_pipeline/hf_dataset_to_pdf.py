import os
import textwrap
from datasets import load_dataset
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ------------------------------------------------------------------
# FORCE OUTPUT TO rag_pipeline/data
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("PDFs will be saved to:", OUTPUT_DIR)

# ------------------------------------------------------------------
# LOAD DATASET
# ------------------------------------------------------------------
dataset = load_dataset(
    "rag-datasets/rag-mini-wikipedia",
    "text-corpus",
    split="passages"
)

print("Dataset columns:", dataset.column_names)

# ------------------------------------------------------------------
# PDF CREATION FUNCTION
# ------------------------------------------------------------------
def save_pdf(text: str, filename: str):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    textobject = c.beginText()
    textobject.setTextOrigin(40, height - 40)
    textobject.setFont("Helvetica", 10)

    for line in textwrap.wrap(text, 90):
        textobject.textLine(line)

    c.drawText(textobject)
    c.showPage()
    c.save()

# ------------------------------------------------------------------
# CREATE PDFs
# ------------------------------------------------------------------
DOCS_TO_CREATE = 50
created = 0

for i, row in enumerate(dataset.select(range(DOCS_TO_CREATE))):
    content = row.get("passage", "").strip()
    if not content:
        continue

    filename = os.path.join(OUTPUT_DIR, f"{i:03d}_wiki_doc_{i}.pdf")
    print("Creating:", filename)
    save_pdf(content, filename)
    created += 1

print(f"\n✅ SUCCESS: {created} PDFs created with REAL pages and extractable text")
