import os
import sys
import unittest
import numpy as np
import cv2
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ai_engine.preprocessor import ImagePreprocessor
from backend.app.ai_engine.detector import PlateDetector
from backend.app.ai_engine.ocr_reader import OCRReader
from backend.app.ai_engine.pipeline import ANPRPipeline
from generate_samples import create_synthetic_plate_image

class TestANPRSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = PROJECT_ROOT / "backend" / "sample_plates"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.test_image_path = str(cls.test_dir / "test_plate.jpg")
        create_synthetic_plate_image("DL01AB1234", cls.test_image_path, (30, 30, 30))

    def test_preprocessor(self):
        img = cv2.imread(self.test_image_path)
        self.assertIsNotNone(img)
        gray = ImagePreprocessor.to_grayscale(img)
        self.assertEqual(len(gray.shape), 2)
        filtered = ImagePreprocessor.apply_bilateral_filter(gray)
        self.assertEqual(filtered.shape, gray.shape)

    def test_detector_candidates(self):
        img = cv2.imread(self.test_image_path)
        candidates = PlateDetector.detect_plate_candidates(img)
        self.assertTrue(len(candidates) > 0)
        x, y, w, h, roi = candidates[0]
        self.assertTrue(w > 0 and h > 0)
        self.assertTrue(roi.size > 0)

    def test_text_cleaning(self):
        raw = " IND-MH-12-DE-1433 "
        cleaned = OCRReader.clean_plate_text(raw)
        self.assertEqual(cleaned, "MH12DE1433")

    def test_pipeline_execution(self):
        img = cv2.imread(self.test_image_path)
        result = ANPRPipeline.process_image(img, source_name="UNIT_TEST")
        self.assertIn("success", result)
        self.assertIn("processing_time_ms", result)
        self.assertTrue(result["processing_time_ms"] > 0)

if __name__ == "__main__":
    unittest.main()
