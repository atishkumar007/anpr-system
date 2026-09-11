import os
import cv2
import time
import uuid
import numpy as np
from typing import Dict, Any, Optional
from backend.app.config import UPLOADS_DIR, OCR_CONFIDENCE_THRESHOLD
from backend.app.ai_engine.preprocessor import ImagePreprocessor
from backend.app.ai_engine.detector import PlateDetector
from backend.app.ai_engine.ocr_reader import OCRReader

class ANPRPipeline:
    """
    Unified end-to-end Automatic Number Plate Recognition (ANPR) pipeline.
    Coordinates detection, OCR, annotation, and snapshot generation.
    """

    @classmethod
    def process_image(cls, image_bgr: np.ndarray, source_name: str = "WEBCAM") -> Dict[str, Any]:
        start_time = time.time()
        result = {
            "success": False,
            "plate_number": None,
            "confidence": 0.0,
            "bounding_box": None,
            "annotated_image_path": None,
            "plate_crop_path": None,
            "processing_time_ms": 0.0,
            "message": "No plate detected"
        }

        if image_bgr is None or image_bgr.size == 0:
            result["message"] = "Invalid or empty image"
            return result

        # 1. Resize if image is huge to optimize speed
        processed_img = ImagePreprocessor.resize_image(image_bgr, max_width=1280)
        img_h, img_w = processed_img.shape[:2]

        # 2. Detect candidate plate regions
        candidates = PlateDetector.detect_plate_candidates(processed_img)

        best_text = ""
        best_conf = 0.0
        best_box = None
        best_crop = None

        # 3. Perform OCR on detected candidate regions
        for (x, y, w, h, roi) in candidates:
            # Clean ROI for OCR
            cleaned_roi = ImagePreprocessor.clean_plate_roi(roi)
            plate_text, conf = OCRReader.extract_text(cleaned_roi)

            # If cleaned roi produced nothing, try raw roi
            if not plate_text:
                plate_text, conf = OCRReader.extract_text(roi)

            if plate_text and len(plate_text) >= 4:
                # Pick detection with longest valid text or highest confidence
                if len(plate_text) > len(best_text) or conf > best_conf:
                    best_text = plate_text
                    best_conf = max(conf, 0.65)  # Set a reasonable minimum for valid text
                    best_box = [x, y, w, h]
                    best_crop = roi

        # Fallback: if no candidates produced text, try OCR on center ROI or full image
        if not best_text:
            plate_text, conf = OCRReader.extract_text(processed_img)
            if plate_text and len(plate_text) >= 4:
                best_text = plate_text
                best_conf = max(conf, 0.60)
                best_box = [0, 0, img_w, img_h]
                best_crop = processed_img

        # 4. Save snapshots and render annotations
        timestamp_str = uuid.uuid4().hex[:8]
        annotated_filename = f"scan_{timestamp_str}.jpg"
        crop_filename = f"crop_{timestamp_str}.jpg"

        annotated_path = os.path.join(UPLOADS_DIR, annotated_filename)
        crop_path = os.path.join(UPLOADS_DIR, crop_filename)

        annotated_img = processed_img.copy()

        if best_text:
            x, y, w, h = best_box
            # Draw bounding box on vehicle image
            color = (0, 215, 0) if best_conf >= OCR_CONFIDENCE_THRESHOLD else (0, 165, 255)
            cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 3)

            # Draw background tag for text
            label = f"{best_text} ({int(best_conf * 100)}%)"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated_img, (x, max(0, y - 30)), (x + tw + 10, y), color, -1)
            cv2.putText(
                annotated_img, label, (x + 5, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA
            )

            # Save cropped plate
            if best_crop is not None and best_crop.size > 0:
                cv2.imwrite(crop_path, best_crop)
                result["plate_crop_path"] = f"/uploads/{crop_filename}"

            result["success"] = True
            result["plate_number"] = best_text
            result["confidence"] = round(best_conf, 2)
            result["bounding_box"] = best_box
            result["message"] = f"Plate recognized: {best_text}"

        # Save annotated image
        cv2.imwrite(annotated_path, annotated_img)
        result["annotated_image_path"] = f"/uploads/{annotated_filename}"
        result["processing_time_ms"] = round((time.time() - start_time) * 1000, 1)

        return result
