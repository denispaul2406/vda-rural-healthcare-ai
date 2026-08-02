from abc import ABC, abstractmethod

class TextToSpeech(ABC):
    """Abstract Base Class for Text-to-Speech Providers in VDA."""
    
    @abstractmethod
    def synthesize(self, text: str, lang_code: str = "en-IN") -> bytes:
        """
        Synthesizes text into audio binary bytes.
        
        Args:
            text: Text to synthesize.
            lang_code: Target spoken language code (e.g. hi-IN, en-IN).
            
        Returns:
            bytes: Audio binary content (WAV/MP3).
        """
        pass
