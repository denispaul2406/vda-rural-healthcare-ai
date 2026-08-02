import os
import logging
from typing import List, Dict, Any, Tuple
import requests

logger = logging.getLogger(__name__)

# Strict System Prompt enforcing RAG-only, no clinical diagnosis/prescription, plain language
VDA_SYSTEM_PROMPT = """
You are a voice-first Virtual Digital Assistant (VDA) for rural Indian health navigation.
Your job is to explain non-communicable disease (NCD) care adherence, medication timing, and follow-up schedules in simple, empathetic, plain language suitable for speech output.

STRICT GUARDRAILS:
1. Ground your response STRICTLY in the provided RETRIEVED PROTOCOL CONTEXT.
2. DO NOT use external medical memory or invent ungrounded details.
3. NEVER prescribe medication, change doses, diagnose symptoms, or interpret clinical lab results.
4. If the retrieved context does not contain the answer, state clearly: "I do not have information on that in my health protocols."
5. Keep your answer brief, friendly, and under 3-4 clear sentences suitable to be spoken aloud over audio.
"""

class Answerer:
    """
    RAG-grounded LLM Answer Generator.
    Synthesizes plain-language patient answers using strictly retrieved protocol context.
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

        # 3. Deterministic Fallback RAG Synthesizer (Local Execution)
        logger.info("[Answerer] Synthesizing grounded response using local RAG protocol rules.")
        top_chunk = retrieved_results[0]["chunk"]
        header = top_chunk["header"]
        text = top_chunk["text"]

        if lang_code.startswith("hi"):
            if "MEDICATION_SCHEDULE" in header:
                ans = "उच्च रक्तचाप और शुगर की दवाई रोज तय समय पर सुबह नाश्ते के बाद लें। बिना डॉक्टर की सलाह के अपनी दवाई बंद या कम न करें।"
            elif "FOLLOW_UP" in header:
                ans = "आपको हर 30 दिन में उप-स्वास्थ्य केंद्र (Sub-Centre / PHC) जाकर अपने ब्लड प्रेशर और शुगर की जांच करानी चाहिए।"
            elif "LIFESTYLE" in header:
                ans = "रोजाना केवल एक छोटा चम्मच (5 ग्राम से कम) नमक खाएं। रोजाना 30 मिनट टहलें और तंबाकू का सेवन बिल्कुल न करें।"
            else:
                ans = f"प्रोटोकॉल निर्देश ({header}): {text[:150]}..."
        else:
            if "HYPERTENSION" in header or "MEDICATION" in header:
                ans = "Take your prescribed anti-hypertensive medication every day at the same time after breakfast. Do not skip or stop doses without consulting your PHC doctor."
            elif "FOLLOW_UP" in header:
                ans = "Please visit your nearest Health and Wellness Centre or Sub-Centre every 30 days for blood pressure monitoring and prescription refills."
            elif "LIFESTYLE" in header:
                ans = "Limit daily salt to less than 1 teaspoon (5g) per day, walk briskly for 30 minutes daily, and completely avoid tobacco."
            else:
                ans = f"According to health protocols ({header}): {text[:150]}..."

        return (ans, source_ids)
