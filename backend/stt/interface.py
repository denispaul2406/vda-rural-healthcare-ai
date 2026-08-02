from abc import ABC, abstractmethod

class SpeechToText(ABC):
    """Abstract Base Class for Speech-to-Text Providers in VDA."""
    
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> tuple[str, str]:
        """
        Transcribes audio bytes into text and detects language.
        
        Args:
            audio_bytes: Raw audio binary data.
            mime_type: MIME type of audio (e.g. audio/wav, audio/webm).
            
        Returns:
            tuple[str, str]: (transcribed_text, detected_language_code)
                             e.g. ("Seene mein dard hai", "hi-IN")
        """
        pass
