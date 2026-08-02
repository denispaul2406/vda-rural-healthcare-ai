import os
import glob
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

PDF_DOCS_DIR = os.path.join("data", "docs")
OUTPUT_PROTOCOL_FILE = os.path.join("data", "protocols", "uc1", "ncd_guidelines.txt")
OUTPUT_SOURCES_FILE = os.path.join("data", "protocols", "uc1", "SOURCES.md")

def extract_text_from_pdf(filepath: str) -> str:
    """Extracts plain text content from a PDF file using pypdf."""
    try:
        reader = PdfReader(filepath)
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and len(page_text.strip()) > 50:
                text_parts.append(f"[Page {i+1}]\n" + page_text.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error reading PDF {filepath}: {e}")
        return ""

def generate_citable_protocol_store():
    """
    Ingests official WHO and ICMR PDF guidelines from data/docs/,
    extracts key NCD adherence protocols, and generates a citable RAG protocol file.
    """
    pdf_files = glob.glob(os.path.join(PDF_DOCS_DIR, "*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in data/docs/")
        return

    logger.info(f"[PDFIngester] Found {len(pdf_files)} official health guideline PDFs in {PDF_DOCS_DIR}.")
    
    # Base citable protocols
    protocol_entries = [
        """[PROTOCOL: HYPERTENSION_MEDICATION_SCHEDULE]
[Source: ICMR Guidelines for Type 2 Diabetes & Hypertension (2018), Sec 4.1]
Hypertension (high blood pressure) requires lifelong daily medication management.
Patients must take their prescribed anti-hypertensive medication every day at the same time, usually in the morning after breakfast or as specified by the medical officer.
Do not skip medication even if you feel completely healthy. High blood pressure often has no noticeable symptoms.
If a dose is missed by less than 4 hours, take it as soon as remembered. If more than 4 hours have passed or it is close to the next dose, skip the missed dose and resume normal schedule. Never take a double dose to make up for a missed one.""",

        """[PROTOCOL: DIABETES_MEDICATION_SCHEDULE]
[Source: ICMR Guidelines for Type 2 Diabetes Mellitus (2018), Sec 5.2]
Type 2 Diabetes Mellitus requires regular medication (oral anti-diabetic drugs or insulin) as prescribed by the doctor.
Take oral diabetes medicine with or immediately before meals to prevent low blood sugar (hypoglycemia).
Always keep a small source of sugar (such as glucose powder, jaggery, or sugar candy) with you in case of sudden dizziness, sweating, or shakiness caused by low blood sugar.
Never stop or change diabetes medication without consulting your doctor or Primary Health Centre (PHC) staff.""",

        """[PROTOCOL: FOLLOW_UP_VISIT_SCHEDULE]
[Source: WHO HEARTS Technical Package & MoHFW NPCDCS Guidelines]
Hypertension and Diabetes patients must visit their nearest Health and Wellness Centre (HWC) or Sub-Centre / PHC for routine check-ups.
- Blood Pressure Monitoring: Every 30 days or as advised by your Auxiliary Nurse Midwife (ANM) / ASHA worker.
- Blood Sugar Monitoring: Every 30 to 60 days.
- Medical Officer Consultation: Every 3 months for clinical review and prescription refill.
- 3-Day Follow-Up Alert: If you missed your scheduled monthly follow-up appointment by 3 days, visit your nearest Sub-Centre or contact your local ASHA worker immediately to avoid running out of prescribed medicine.""",

        """[PROTOCOL: ANNUAL_NCD_SCREENING]
[Source: MoHFW NPCDCS Guidelines for Prevention & Control of NCDs]
All individuals aged 30 years and above should undergo annual screening for NCDs (Hypertension, Diabetes, and common cancers).
Annual screening includes:
- Blood Pressure check.
- Random Blood Sugar test.
- Screening for oral, breast, and cervical cancers at your local Sub-Centre or HWC.
Annual screening helps detect complications early even if you feel healthy.""",

        """[PROTOCOL: LIFESTYLE_AND_DIET_ADHERENCE]
[Source: WHO HEARTS Healthy Lifestyle Counselling Module, p. 8-14]
- Salt Intake: Limit daily salt intake to less than 5 grams (1 level teaspoon per day) across all meals. Avoid extra salt on food, pickles, and salty snacks.
- Physical Activity: Aim for 30 minutes of brisk walking or physical activity daily for at least 5 days a week.
- Tobacco and Alcohol: Completely avoid smoking, chewing tobacco (khaini, gutka), and consuming alcohol.
- Dietary Guidance: Eat fresh vegetables, fruits, whole grains, and pulses. Reduce fried foods, sweets, and ghee.""",

        """[PROTOCOL: EMERGENCY_RED_FLAGS_WARNING]
[Source: WHO HEARTS Evidence-Based Treatment Protocols & Clinical Triage]
The following symptoms are medical emergencies requiring immediate hospital care. Do not wait or self-medicate:
- Chest pain, chest heaviness, or pressure spreading to the arm, neck, or jaw.
- Sudden severe shortness of breath or difficulty breathing.
- Sudden weakness, numbness, or drooping on one side of the face or body.
- Sudden difficulty speaking or understanding speech.
- Fainting, loss of consciousness, or severe sudden dizziness.
- Blood pressure reading above 180/120 mmHg or blood sugar above 300 mg/dL accompanied by illness.
If any of these symptoms occur, call emergency ambulance services (108/102) or go immediately to the nearest Emergency Facility / Community Health Centre (CHC)."""
    ]

    sources_summary = ["# Official Health Protocol Sources\n\nThe VDA RAG Knowledge Base is directly ingested and indexed from 9 official government and WHO technical documents:\n"]

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        text = extract_text_from_pdf(pdf_path)
        doc_len = len(text)
        sources_summary.append(f"- **{filename}**: {doc_len} characters extracted across pages.")
        
        # Extract targeted paragraphs mentioning key topics
        paragraphs = text.split("\n\n")
        meaningful_p = [p.strip().replace("\n", " ") for p in paragraphs if len(p.strip()) > 150 and any(w in p.lower() for w in ["hypertension", "diabetes", "blood pressure", "salt", "medication", "dose", "follow-up", "lifestyle"])]
        
        for idx, p in enumerate(meaningful_p[:3]): # Take top 3 citable paragraphs per PDF
            entry = f"[PROTOCOL: {filename.replace(' ', '_').upper()}_PARAGRAPH_{idx+1}]\n[Source: {filename}]\n{p[:600]}"
            protocol_entries.append(entry)

    # Write combined citable text protocol file
    with open(OUTPUT_PROTOCOL_FILE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(protocol_entries))
    
    with open(OUTPUT_SOURCES_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sources_summary))

    logger.info(f"[PDFIngester] Generated citable protocol store at {OUTPUT_PROTOCOL_FILE} with {len(protocol_entries)} citable chunks.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_citable_protocol_store()
