import cv2
import numpy as np

class ImagePreprocessor:
    """
    Handles image preprocessing for license plate detection and OCR.
    Optimized for varying lighting, contrast, angles, and noise.
    """

    @staticmethod
    def resize_image(image: np.ndarray, max_width: int = 1280) -> np.ndarray:
        h, w = image.shape[:2]
        if w > max_width:
            scale = max_width / float(w)
            return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return image

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    @staticmethod
    def apply_bilateral_filter(gray: np.ndarray) -> np.ndarray:
        """Smooths image while preserving sharp character and plate edges."""
        return cv2.bilateralFilter(gray, 11, 17, 17)

    @staticmethod
    def enhance_contrast(gray: np.ndarray) -> np.ndarray:
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    @staticmethod
    def get_morphological_edges(gray: np.ndarray) -> np.ndarray:
        """Finds horizontal and vertical edge regions typical of license plates."""
        # Blackhat transform to reveal dark elements on light background or vice-versa
        rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)

        # Sobel gradient along X axis
        grad_x = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        grad_x = np.absolute(grad_x)
        (min_val, max_val) = (np.min(grad_x), np.max(grad_x))
        if max_val - min_val > 0:
            grad_x = (255 * ((grad_x - min_val) / (max_val - min_val))).astype("uint8")
        else:
            grad_x = grad_x.astype("uint8")

        # Blur and close regions to connect plate characters
        grad_x = cv2.GaussianBlur(grad_x, (5, 5), 0)
        grad_x = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, rect_kernel)
        _, thresh = cv2.threshold(grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Erode & dilate to eliminate small noise artifacts
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)
        return thresh

    @staticmethod
    def clean_plate_roi(plate_roi: np.ndarray) -> np.ndarray:
        """Prepares a cropped plate region for high-accuracy OCR."""
        gray = ImagePreprocessor.to_grayscale(plate_roi)
        # Upscale small plates for sharper character recognition
        h, w = gray.shape
        if h < 60:
            scale = 80.0 / max(h, 1)
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        # Adaptive thresholding to binarize plate text cleanly
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 19, 9
        )
        return binary
