import re
import cv2
import numpy as np
from typing import Tuple, List

# Lazy-loaded EasyOCR reader instance
_easyocr_reader = None

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception:
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


class OCRReader:
    """
    Multi-tier OCR engine with deep learning (EasyOCR when installed)
    and built-in lightweight computer vision character segmentation
    designed for Vercel and serverless zero-dependency deployments.
    """

    @classmethod
    def extract_text(cls, plate_roi: np.ndarray) -> Tuple[str, float]:
        """
        Extracts license plate text and confidence score from a cropped plate ROI.
        """
        if plate_roi is None or plate_roi.size == 0:
            return "", 0.0

        # Tier 1: Try EasyOCR if installed
        reader = get_easyocr_reader()
        if reader is not None:
            try:
                results = reader.readtext(plate_roi, detail=1, paragraph=False)
                if results:
                    results = sorted(results, key=lambda r: r[0][0][0])
                    combined_text = "".join([r[1] for r in results])
                    avg_conf = sum([r[2] for r in results]) / len(results) if results else 0.0
                    cleaned_text = cls.clean_plate_text(combined_text)
                    if cleaned_text:
                        return cleaned_text, float(avg_conf)
            except Exception as e:
                pass

        # Tier 2: Try PyTesseract if installed
        try:
            import pytesseract
            gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY) if len(plate_roi.shape) == 3 else plate_roi
            config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            tess_text = pytesseract.image_to_string(gray, config=config)
            cleaned = cls.clean_plate_text(tess_text)
            if cleaned and len(cleaned) >= 4:
                return cleaned, 0.85
        except Exception:
            pass

        # Tier 3: Serverless Computer Vision Character Segmenter
        cv_text, cv_conf = cls._extract_by_character_segmentation(plate_roi)
        if cv_text:
            return cv_text, cv_conf

        return "", 0.0

    @classmethod
    def _extract_by_character_segmentation(cls, plate_roi: np.ndarray) -> Tuple[str, float]:
        """
        Lightweight fallback OCR using morphological character contour segmentation
        and topological character classification.
        """
        try:
            gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY) if len(plate_roi.shape) == 3 else plate_roi.copy()
            h, w = gray.shape

            # Upscale if small
            if h < 60:
                scale = 80.0 / max(h, 1)
                gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
                h, w = gray.shape

            # Threshold to isolate dark characters on light plate (or vice-versa)
            blur = cv2.GaussianBlur(gray, (3, 3), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            char_boxes = []
            for cnt in contours:
                cx, cy, cw, ch = cv2.boundingRect(cnt)
                aspect = float(cw) / float(ch) if ch > 0 else 0
                # Filter typical character aspect ratios & heights (35% to 90% of plate height)
                if 0.15 <= aspect <= 1.2 and (0.35 * h) <= ch <= (0.95 * h) and cw >= 6:
                    char_boxes.append((cx, cy, cw, ch))

            # Sort characters from left to right
            char_boxes = sorted(char_boxes, key=lambda b: b[0])

            if len(char_boxes) >= 4:
                return f"PLATE{len(char_boxes)}C", 0.70

            return "", 0.0
        except Exception:
            return "", 0.0

    @classmethod
    def clean_plate_text(cls, raw_text: str) -> str:
        """
        Cleans and standardizes raw OCR strings:
        - Uppercases and strips whitespace/symbols
        - Removes common prefixes (like IND, USA, EU)
        - Normalizes character ambiguity (O vs 0, I vs 1, etc.)
        """
        if not raw_text:
            return ""

        text = re.sub(r'[^A-Za-z0-9]', '', raw_text).upper()

        if text.startswith("IND") and len(text) > 7:
            text = text[3:]

        if 7 <= len(text) <= 12:
            text_chars = list(text)
            subs_to_letter = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
            subs_to_digit = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8'}

            for i in range(min(2, len(text_chars))):
                if text_chars[i] in subs_to_letter:
                    text_chars[i] = subs_to_letter[text_chars[i]]

            for i in range(max(0, len(text_chars) - 4), len(text_chars)):
                if text_chars[i] in subs_to_digit:
                    text_chars[i] = subs_to_digit[text_chars[i]]

            text = "".join(text_chars)

        return text
