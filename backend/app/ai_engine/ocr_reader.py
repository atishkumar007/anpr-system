import re
import cv2
import numpy as np
from typing import Tuple, Optional

# Lazy-loaded EasyOCR reader instance
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            # Initialize with English, GPU if available otherwise CPU
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            print(f"[OCR] EasyOCR initialization warning: {e}")
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


class OCRReader:
    """
    Robust OCR Engine with deep learning (EasyOCR), Tesseract fallback,
    and specialized post-processing regex filters for license plates.
    """

    @classmethod
    def extract_text(cls, plate_roi: np.ndarray) -> Tuple[str, float]:
        """
        Extracts license plate text and confidence score from a cropped plate ROI.
        """
        if plate_roi is None or plate_roi.size == 0:
            return "", 0.0

        # Try EasyOCR first
        reader = get_easyocr_reader()
        if reader is not None:
            try:
                results = reader.readtext(plate_roi, detail=1, paragraph=False)
                if results:
                    # Sort detections from left to right
                    results = sorted(results, key=lambda r: r[0][0][0])
                    combined_text = "".join([r[1] for r in results])
                    avg_conf = sum([r[2] for r in results]) / len(results) if results else 0.0

                    cleaned_text = cls.clean_plate_text(combined_text)
                    if cleaned_text:
                        return cleaned_text, float(avg_conf)
            except Exception as e:
                print(f"[OCR] EasyOCR read error: {e}")

        # Fallback to Tesseract if installed
        try:
            import pytesseract
            gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY) if len(plate_roi.shape) == 3 else plate_roi
            config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            tess_text = pytesseract.image_to_string(gray, config=config)
            cleaned = cls.clean_plate_text(tess_text)
            if cleaned:
                return cleaned, 0.75
        except Exception:
            pass

        # Fallback: Basic character count & morphology heuristic
        return "", 0.0

    @classmethod
    def clean_plate_text(cls, raw_text: str) -> str:
        """
        Cleans and standardizes raw OCR strings:
        - Uppercases and strips whitespace/symbols
        - Removes common prefixes (like IND, USA, EU, etc.)
        - Normalizes character ambiguity based on position patterns
        """
        if not raw_text:
            return ""

        # Remove non-alphanumeric characters
        text = re.sub(r'[^A-Za-z0-9]', '', raw_text).upper()

        # Remove common country/state watermark tags
        if text.startswith("IND") and len(text) > 7:
            text = text[3:]

        # Common OCR character substitutions when expected
        # E.g. Standard format: 2 Letters (State) + 2 Digits (District) + Letters + 4 Digits
        # Example: DL01AB1234 or MH12DE1433 or CA7ABC123
        if len(text) >= 8 and len(text) <= 12:
            text_chars = list(text)
            # First 2 should be letters in many standard formats (if currently 0/1/8, convert)
            subs_to_letter = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
            subs_to_digit = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8'}

            # First 2 chars -> often letters
            for i in range(min(2, len(text_chars))):
                if text_chars[i] in subs_to_letter:
                    text_chars[i] = subs_to_letter[text_chars[i]]

            # Last 4 chars -> often digits in vehicle plates
            if len(text_chars) >= 6:
                for i in range(len(text_chars) - 4, len(text_chars)):
                    if text_chars[i] in subs_to_digit:
                        text_chars[i] = subs_to_digit[text_chars[i]]

            text = "".join(text_chars)

        return text
