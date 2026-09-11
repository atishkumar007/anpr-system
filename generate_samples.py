import os
import cv2
import numpy as np
from pathlib import Path

def create_synthetic_plate_image(plate_text: str, output_path: str, vehicle_color=(45, 45, 50)):
    """
    Renders a realistic vehicle bumper frame containing a clearly styled license plate.
    """
    # 1. Canvas Dimensions (Vehicle frontal / rear bumper section)
    img_w, img_h = 700, 420
    canvas = np.full((img_h, img_w, 3), vehicle_color, dtype=np.uint8)

    # Add vehicle grille / bumper shading gradient
    for y in range(img_h):
        factor = 0.7 + 0.3 * (y / img_h)
        canvas[y, :] = (np.array(vehicle_color) * factor).astype(np.uint8)

    # Vehicle grille lines above plate
    for gy in range(40, 160, 20):
        cv2.line(canvas, (80, gy), (img_w - 80, gy), (25, 25, 25), 6)
        cv2.line(canvas, (80, gy + 3), (img_w - 80, gy + 3), (65, 65, 70), 2)

    # 2. License Plate Holder Dimensions
    plate_w, plate_h = 420, 110
    plate_x = (img_w - plate_w) // 2
    plate_y = 220

    # Black Holder Border
    cv2.rectangle(canvas, (plate_x - 10, plate_y - 10), (plate_x + plate_w + 10, plate_y + plate_h + 10), (15, 15, 15), -1)
    cv2.rectangle(canvas, (plate_x - 10, plate_y - 10), (plate_x + plate_w + 10, plate_y + plate_h + 10), (80, 80, 80), 2)

    # Plate Background (White/Off-white reflective acrylic)
    plate_bg = np.full((plate_h, plate_w, 3), (245, 245, 248), dtype=np.uint8)

    # Left Blue Band (Euro / Standard International / IND strip)
    strip_w = 42
    cv2.rectangle(plate_bg, (0, 0), (strip_w, plate_h), (180, 50, 20), -1) # Blue band in BGR

    # Small emblem/IND text on strip
    cv2.putText(plate_bg, "IND", (6, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.circle(plate_bg, (21, 35), 8, (255, 215, 0), -1) # Golden chakra / star emblem

    # Outer thin plate border
    cv2.rectangle(plate_bg, (0, 0), (plate_w - 1, plate_h - 1), (20, 20, 20), 3)

    # Text Placement
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1.65
    thickness = 3

    # Format text with space in middle if long
    display_text = plate_text
    if len(plate_text) >= 10:
        display_text = f"{plate_text[:4]} {plate_text[4:]}"

    (tw, th), _ = cv2.getTextSize(display_text, font, font_scale, thickness)
    tx = strip_w + ((plate_w - strip_w - tw) // 2)
    ty = (plate_h + th) // 2

    # Draw plate text shadow + main embossed text
    cv2.putText(plate_bg, display_text, (tx + 1, ty + 1), font, font_scale, (100, 100, 100), thickness, cv2.LINE_AA)
    cv2.putText(plate_bg, display_text, (tx, ty), font, font_scale, (10, 10, 10), thickness, cv2.LINE_AA)

    # Screw bolts
    cv2.circle(plate_bg, (strip_w + 25, 20), 4, (120, 120, 120), -1)
    cv2.circle(plate_bg, (plate_w - 25, 20), 4, (120, 120, 120), -1)
    cv2.circle(plate_bg, (strip_w + 25, plate_h - 20), 4, (120, 120, 120), -1)
    cv2.circle(plate_bg, (plate_w - 25, plate_h - 20), 4, (120, 120, 120), -1)

    # Composite plate into canvas
    canvas[plate_y:plate_y + plate_h, plate_x:plate_x + plate_w] = plate_bg

    # Save image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, canvas)
    print(f"Generated sample: {output_path}")

def generate_all_samples():
    base_dir = Path(__file__).resolve().parent
    samples_dir = base_dir / "backend" / "sample_plates"
    samples_dir.mkdir(parents=True, exist_ok=True)

    test_samples = [
        ("MH12DE1433", "car_whitelisted_1.jpg", (25, 25, 25)),    # Black Luxury SUV
        ("DL01AB1234", "car_whitelisted_2.jpg", (180, 180, 190)),# Silver Sedan
        ("KA05MJ9876", "car_whitelisted_3.jpg", (30, 80, 140)),  # Blue Hatchback
        ("HR26DK8392", "car_blacklisted_1.jpg", (20, 20, 160)),  # Red Sports Car
        ("TN09AZ4321", "car_guest_vendor.jpg",  (120, 120, 120)),# Grey Delivery Van
        ("UP16AB9999", "car_unregistered.jpg",  (200, 200, 210)),# White SUV
        ("MH04EF5555", "car_executive.jpg",     (40, 70, 40)),   # Green Sedan
        ("DL08CA2020", "car_visitor.jpg",       (35, 35, 35)),   # Dark Grey Car
    ]

    for plate, filename, color in test_samples:
        out_path = str(samples_dir / filename)
        create_synthetic_plate_image(plate, out_path, color)

if __name__ == "__main__":
    generate_all_samples()
