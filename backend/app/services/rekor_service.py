import os
import requests
import base64
from typing import Dict, Any, Optional

class ExternalANPRService:
    """
    Integrates with official external ANPR & Vehicle intelligence APIs
    (Rekor CarCheck / OpenALPR, ANPR.software, and RapidAPI RTO)
    for benchmarking against the local AI model.
    """

    @staticmethod
    def call_rekor_carcheck(image_bytes: bytes, api_key: str, country: str = "in") -> Optional[Dict[str, Any]]:
        """
        Calls Rekor CarCheck (OpenALPR Cloud API).
        Docs: https://api.openalpr.com/v2/recognize
        """
        try:
            url = f"https://api.openalpr.com/v2/recognize?secret_key={api_key}&recognize_vehicle=1&country={country}"
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            res = requests.post(url, data=img_b64, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=8)
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                if results:
                    top = results[0]
                    v_info = top.get("vehicle", {})
                    v_make = v_info.get("make_model", [{}])[0].get("name", "Unknown") if v_info.get("make_model") else "Unknown"
                    v_color = v_info.get("color", [{}])[0].get("name", "Unknown") if v_info.get("color") else "Unknown"
                    v_body = v_info.get("body_type", [{}])[0].get("name", "Car") if v_info.get("body_type") else "Car"

                    return {
                        "success": True,
                        "provider": "REKOR_CARCHECK_API",
                        "plate_number": top.get("plate", ""),
                        "confidence": round(float(top.get("confidence", 0.0)) / 100.0, 2),
                        "vehicle_type": v_body.capitalize(),
                        "vehicle_color": v_color.capitalize(),
                        "vehicle_model": v_make.title()
                    }
        except Exception as e:
            print(f"[Rekor API] Error: {e}")
        return None

    @staticmethod
    def call_anpr_software(image_bytes: bytes, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Calls ANPR.software Cloud OCR API.
        """
        try:
            url = "https://api.anpr.software/v1/recognize"
            files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
            headers = {"Authorization": f"Bearer {api_key}"}
            res = requests.post(url, files=files, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if "plate" in data:
                    return {
                        "success": True,
                        "provider": "ANPR_SOFTWARE_API",
                        "plate_number": data.get("plate"),
                        "confidence": float(data.get("confidence", 0.9)),
                        "vehicle_type": data.get("vehicle_type", "Car"),
                        "vehicle_color": data.get("vehicle_color", "White")
                    }
        except Exception as e:
            print(f"[ANPR.software] Error: {e}")
        return None
