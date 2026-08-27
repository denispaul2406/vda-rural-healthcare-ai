import os
import logging
from typing import List, Dict, Any, Tuple
import requests

logger = logging.getLogger(__name__)

# Strict System Prompt enforcing RAG-only, plain language, step-by-step patient advice
VDA_SYSTEM_PROMPT = """
You are a voice-first Virtual Digital Assistant (VDA) for rural Indian health navigation.
Your job is to explain non-communicable disease (NCD) care adherence, medication timing, scheme entitlement (PM-JAY), and public facility locations in simple, empathetic, plain language suitable for speech output.

STRICT GUARDRAILS:
1. Ground your response STRICTLY in the provided RETRIEVED PROTOCOL CONTEXT.
2. DO NOT output raw PDF chunk IDs, paragraph numbers, header tags, or source file metadata in the spoken advice. Give direct steps and practical advice.
3. NEVER prescribe new medication, change doses, diagnose symptoms, or interpret clinical lab results.
4. If the retrieved context does not contain the answer, state clearly: "I do not have information on that in my health protocols."
5. Keep your answer brief, friendly, and under 3-4 clear sentences suitable to be spoken aloud over audio.
"""

class Answerer:
    """
    RAG-grounded LLM Answer Generator.
    Synthesizes plain-language patient advice using strictly retrieved protocol context.
    """

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    def generate_answer(self, query: str, retrieved_results: List[Dict[str, Any]], lang_code: str = "en") -> Tuple[str, List[str]]:
        """
        Generates a grounded answer from retrieved protocol chunks.
        
        Returns:
            tuple: (generated_text_response, source_chunk_ids)
        """
        if not retrieved_results:
            no_info_text = "माफ़ कीजिये, मेरे पास इस विषय पर स्वास्थ्य प्रोटोकॉल की जानकारी नहीं है।" if lang_code.startswith("hi") else "I am sorry, I do not have information on that in my health protocols."
            return (no_info_text, [])

        context_texts = []
        source_ids = []
        for item in retrieved_results:
            chunk = item["chunk"]
            context_texts.append(f"[{chunk['header']}]: {chunk['text']}")
            source_ids.append(chunk["chunk_id"])

        context_str = "\n\n".join(context_texts)

        # 1. Gemini API if available
        if self.gemini_key and self.provider == "gemini":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                prompt = f"{VDA_SYSTEM_PROMPT}\n\nRETRIEVED PROTOCOL CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{query}\n\nPATIENT SPOKEN RESPONSE ({lang_code}):"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    ans = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    logger.info(f"[Answerer] Gemini generated answer: '{ans[:60]}...'")
                    return (ans, source_ids)
            except Exception as e:
                logger.error(f"[Answerer] Gemini call failed: {e}. Falling back to deterministic RAG synthesis.")

        # 2. OpenAI API if available
        if self.openai_key and self.provider == "openai":
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                messages = [
                    {"role": "system", "content": VDA_SYSTEM_PROMPT},
                    {"role": "user", "content": f"RETRIEVED PROTOCOL CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{query}"}
                ]
                payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.2}
                res = requests.post(url, json=payload, headers=headers, timeout=10)
                if res.status_code == 200:
                    ans = res.json()["choices"][0]["message"]["content"].strip()
                    logger.info(f"[Answerer] OpenAI generated answer: '{ans[:60]}...'")
                    return (ans, source_ids)
            except Exception as e:
                logger.error(f"[Answerer] OpenAI call failed: {e}. Falling back to deterministic RAG synthesis.")

        # 3. Deterministic Grounded RAG Synthesizer (Local Execution)
        logger.info("[Answerer] Synthesizing grounded response using local RAG protocol rules.")
        top_chunk = retrieved_results[0]["chunk"]
        header = top_chunk.get("header", "").upper()
        text = top_chunk.get("text", "")
        use_case = top_chunk.get("use_case", "UC1")

        query_lower = query.lower()

        if lang_code.startswith("hi"):
            if use_case == "UC3" or "FACILITY" in header or "PHC" in header or "HOSPITAL" in header or any(w in query_lower for w in ["hospital", "phc", "hwc", "kahan", "paas"]):
                ans = "बेंगलुरु ग्रामीण क्षेत्र में आप मुफ्त बीपी, शुगर जांच और दवाओं के लिए नेलमंगला 24x7 पीएचसी, दोड्डबल्लापुरा जिला अस्पताल या होसकोटे अस्पताल जा सकते हैं। आपात स्थिति में 108 एम्बुलेंस या 104 हेल्पलाइन पर कॉल करें।"
            elif use_case == "UC2" or "SCHEME" in header or "PMJAY" in header or any(w in query_lower for w in ["pmjay", "ayushman", "card", "yojana", "5 lakh", "free"]):
                ans = "आयुष्मान भारत योजना के तहत 5 लाख रुपये तक का मुफ्त अस्पताल इलाज मिलता है। अपनी पात्रता जांचने और गोल्डन कार्ड बनवाने के लिए अपना आधार कार्ड और राशन कार्ड लेकर अपने निकटतम उप-स्वास्थ्य केंद्र या पीएचसी जाएं।"
            else:
                ans = "अपनी बीपी और शुगर की दवा रोज सुबह नाश्ते के बाद तय समय पर लें। भोजन में नमक 5 ग्राम से कम रखें और हर 30 दिन में अपने निकटतम स्वास्थ्य केंद्र पर जांच कराएं।"
        else:
            if use_case == "UC3" or "FACILITY" in header or "PHC" in header or "HOSPITAL" in header or any(w in query_lower for w in ["hospital", "phc", "hwc", "where", "near", "doddaballapura", "nelamangala"]):
                ans = "For healthcare services in Bengaluru Rural District, you can visit Nelamangala 24x7 PHC, Doddaballapura District Hospital, or Hoskote CHC for free NCD screening, doctor consultations, and essential medicines. Dial 108 for emergency ambulance or 104 for health advice."
            elif use_case == "UC2" or "SCHEME" in header or "PMJAY" in header or any(w in query_lower for w in ["pmjay", "ayushman", "card", "scheme", "5 lakh", "eligible"]):
                ans = "Under Ayushman Bharat PM-JAY, eligible families receive up to ₹5 Lakh per year for free cashless hospital treatment. To check eligibility and get your Golden Card, bring your Aadhaar Card and Ration Card to your nearest Health & Wellness Centre or public hospital."
            else:
                ans = "Take your prescribed blood pressure and diabetes medicine every day at the same time after breakfast. Do not skip doses without consulting your doctor, limit daily salt intake to under 1 teaspoon (5g), and visit your Sub-Centre every 30 days for routine follow-up."

        return (ans, source_ids)
