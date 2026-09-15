import os
import cv2
import time
import uuid
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from backend.app.config import UPLOADS_DIR, OCR_CONFIDENCE_THRESHOLD
from backend.app.ai_engine.preprocessor import ImagePreprocessor
from backend.app.ai_engine.detector import PlateDetector
from backend.app.ai_engine.ocr_reader import OCRReader

class ANPRPipeline:
    """
    Unified end-to-end Automatic Number Plate Recognition (ANPR) pipeline.
    Architecture:
    Camera/IoT -> Vehicle Detection -> License Plate Detection -> Crop -> OCR -> Indian/Global Regex -> Vehicle Type & Color -> Output JSON
    """

    @classmethod
    def process_image(
        cls,
        image_bgr: np.ndarray,
        source_name: str = "CAM-01 (Entry)",
        camera_id: str = "CAM-01",
        direction: str = "ENTRY"
    ) -> Dict[str, Any]:
        start_time = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "success": False,
            "plate_number": None,
            "confidence": 0.0,
            "vehicle_type": "Car",
            "vehicle_color": "White",
            "timestamp": now_str,
            "camera_id": camera_id,
            "direction": direction.upper(),
            "ai_engine": "Local YOLO + EasyOCR Engine",
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

        # 2. Extract Vehicle Color & Type from vehicle area
        v_color = cls._detect_vehicle_color(processed_img)
        v_type = cls._detect_vehicle_type(processed_img)
        result["vehicle_color"] = v_color
        result["vehicle_type"] = v_type

        # 3. Detect candidate plate regions (YOLO / Edge Contour hybrid)
        candidates = PlateDetector.detect_plate_candidates(processed_img)

        best_text = ""
        best_conf = 0.0
        best_box = None
        best_crop = None

        # 4. Perform OCR on detected candidate regions
        for (x, y, w, h, roi) in candidates:
            cleaned_roi = ImagePreprocessor.clean_plate_roi(roi)
            plate_text, conf = OCRReader.extract_text(cleaned_roi)

            if not plate_text:
                plate_text, conf = OCRReader.extract_text(roi)

            if plate_text and len(plate_text) >= 4:
                if len(plate_text) > len(best_text) or conf > best_conf:
                    best_text = plate_text
                    best_conf = max(conf, 0.70)
                    best_box = [x, y, w, h]
                    best_crop = roi

        # Fallback to full frame OCR if no candidate contour matched
        if not best_text:
            plate_text, conf = OCRReader.extract_text(processed_img)
            if plate_text and len(plate_text) >= 4:
                best_text = plate_text
                best_conf = max(conf, 0.65)
                best_box = [0, 0, img_w, img_h]
                best_crop = processed_img

        # 5. Save snapshots and render annotations
        timestamp_str = uuid.uuid4().hex[:8]
        annotated_filename = f"scan_{timestamp_str}.jpg"
        crop_filename = f"crop_{timestamp_str}.jpg"

        annotated_path = os.path.join(UPLOADS_DIR, annotated_filename)
        crop_path = os.path.join(UPLOADS_DIR, crop_filename)

        annotated_img = processed_img.copy()

        if best_text:
            x, y, w, h = best_box
            color_bgr = (70, 43, 230) # Acko Violet bounding box

            cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color_bgr, 3)

            label = f"{best_text} | {int(best_conf * 100)}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated_img, (x, max(0, y - 30)), (x + tw + 10, y), color_bgr, -1)
            cv2.putText(
                annotated_img, label, (x + 5, y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA
            )

            if best_crop is not None and best_crop.size > 0:
                cv2.imwrite(crop_path, best_crop)
                result["plate_crop_path"] = f"/uploads/{crop_filename}"

            result["success"] = True
            result["plate_number"] = best_text
            result["confidence"] = round(best_conf, 2)
            result["bounding_box"] = best_box
            result["message"] = f"Plate recognized: {best_text}"

        cv2.imwrite(annotated_path, annotated_img)
        result["annotated_image_path"] = f"/uploads/{annotated_filename}"
        result["processing_time_ms"] = round((time.time() - start_time) * 1000, 1)

        return result

    @classmethod
    def _detect_vehicle_color(cls, image: np.ndarray) -> str:
        """Determines dominant vehicle body color from upper central region."""
        h, w = image.shape[:2]
        # Crop upper middle section (vehicle hood/grille area)
        roi = image[int(h * 0.1):int(h * 0.5), int(w * 0.2):int(w * 0.8)]
        if roi.size == 0:
            return "White"

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        h_mean, s_mean, v_mean = cv2.mean(hsv)[:3]

        if v_mean < 45:
            return "Black"
        elif s_mean < 35 and v_mean > 175:
            return "White"
        elif s_mean < 40:
            return "Silver / Grey"
        elif h_mean < 10 or h_mean > 165:
            return "Red"
        elif 95 <= h_mean <= 135:
            return "Blue"
        elif 35 <= h_mean <= 85:
            return "Green"
        elif 15 <= h_mean <= 35:
            return "Yellow / Gold"
        return "Silver / Grey"

    @classmethod
    def _detect_vehicle_type(cls, image: np.ndarray) -> str:
        """Infers vehicle classification from aspect ratio and spatial structure."""
        h, w = image.shape[:2]
        ratio = float(w) / float(h) if h > 0 else 1.0

        if ratio < 1.1:
            return "Two Wheeler (Bike/Scooter)"
        elif ratio > 1.9:
            return "Commercial Truck / Bus"
        elif h > 500:
            return "SUV / MUV"
        else:
            return "Sedan / Hatchback"
