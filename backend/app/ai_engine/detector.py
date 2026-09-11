import cv2
import numpy as np
from typing import List, Tuple, Optional
from backend.app.ai_engine.preprocessor import ImagePreprocessor

class PlateDetector:
    """
    Detects and localizes vehicle license plates within raw frames/images
    using computer vision contour analysis, edge filtering, and aspect ratio heuristics.
    """

    MIN_ASPECT_RATIO = 1.6
    MAX_ASPECT_RATIO = 6.5
    MIN_AREA = 800
    MAX_AREA_RATIO = 0.5

    @classmethod
    def detect_plate_candidates(cls, image: np.ndarray) -> List[Tuple[int, int, int, int, np.ndarray]]:
        """
        Locates candidate license plate regions.
        Returns a list of tuples: (x, y, w, h, cropped_plate_image), ordered by likelihood.
        """
        img_h, img_w = image.shape[:2]
        gray = ImagePreprocessor.to_grayscale(image)
        filtered = ImagePreprocessor.apply_bilateral_filter(gray)
        enhanced = ImagePreprocessor.enhance_contrast(filtered)

        # Method 1: Canny edge based detection
        edges = cv2.Canny(enhanced, 100, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for cnt in contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / float(h) if h > 0 else 0
            area = w * h

            if (
                cls.MIN_ASPECT_RATIO <= aspect_ratio <= cls.MAX_ASPECT_RATIO
                and area >= cls.MIN_AREA
                and area <= (img_h * img_w * cls.MAX_AREA_RATIO)
            ):
                # Add padding around detected ROI
                pad_x = int(w * 0.05)
                pad_y = int(h * 0.08)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(img_w, x + w + pad_x)
                y2 = min(img_h, y + h + pad_y)

                roi = image[y1:y2, x1:x2]
                if roi.size > 0:
                    candidates.append((x1, y1, x2 - x1, y2 - y1, roi))

        # Method 2: Morphological gradient candidates
        morph_thresh = ImagePreprocessor.get_morphological_edges(enhanced)
        m_contours, _ = cv2.findContours(morph_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in m_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / float(h) if h > 0 else 0
            area = w * h
            if (
                cls.MIN_ASPECT_RATIO <= aspect_ratio <= cls.MAX_ASPECT_RATIO
                and area >= cls.MIN_AREA
                and area <= (img_h * img_w * cls.MAX_AREA_RATIO)
            ):
                pad_x = int(w * 0.05)
                pad_y = int(h * 0.08)
                x1 = max(0, x - pad_x)
                y1 = max(0, y - pad_y)
                x2 = min(img_w, x + w + pad_x)
                y2 = min(img_h, y + h + pad_y)
                roi = image[y1:y2, x1:x2]
                if roi.size > 0:
                    candidates.append((x1, y1, x2 - x1, y2 - y1, roi))

        # Deduplicate overlapping bounding boxes (NMS-like overlap reduction)
        unique_candidates = cls._non_max_suppression(candidates)

        # Fallback: If image itself is a cropped plate or tight shot
        if not unique_candidates:
            whole_aspect = float(img_w) / float(img_h) if img_h > 0 else 1
            if cls.MIN_ASPECT_RATIO <= whole_aspect <= cls.MAX_ASPECT_RATIO or img_w < 800:
                unique_candidates.append((0, 0, img_w, img_h, image))

        return unique_candidates

    @staticmethod
    def _non_max_suppression(boxes: List[Tuple[int, int, int, int, np.ndarray]], overlap_thresh: float = 0.4):
        if not boxes:
            return []

        # Sort by area descending
        boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
        keep = []

        for b in boxes:
            x, y, w, h, roi = b
            overlap = False
            for kx, ky, kw, kh, _ in keep:
                # Calculate Intersection over Union (IoU)
                xx1 = max(x, kx)
                yy1 = max(y, ky)
                xx2 = min(x + w, kx + kw)
                yy2 = min(y + h, ky + kh)

                inter_w = max(0, xx2 - xx1)
                inter_h = max(0, yy2 - yy1)
                inter_area = inter_w * inter_h
                box_area = w * h

                if box_area > 0 and (inter_area / float(box_area)) > overlap_thresh:
                    overlap = True
                    break

            if not overlap:
                keep.append(b)

        return keep
