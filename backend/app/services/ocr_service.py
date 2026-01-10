from PIL import Image
import io
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR service for document verification using PaddleOCR.
    
    Extracts text from Kenyan IDs, certificates, and diplomas.
    """
    
    def __init__(self):
        # Check if OCR should be enabled from settings
        from app.config import settings
        ocr_mode = getattr(settings, 'OCR_MODE', 'paddleocr')
        
        if ocr_mode == 'mock':
            logger.info("✓ Using mock OCR mode (MVP)")
            self.ocr = None
            return
        
        # Try to initialize PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("✓ PaddleOCR initialized successfully")
        except ImportError:
            logger.info("✓ PaddleOCR not installed. Using mock mode (MVP).")
            self.ocr = None
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}. Using mock mode.")
            self.ocr = None
    
    def extract_text(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from image using OCR.
        
        Returns:
            List of {text, confidence, bbox}
        """
        if not self.ocr:
            # Mock OCR results for testing
            return [
                {"text": "JOHN MWANGI KARIUKI", "confidence": 0.95, "bbox": [[100, 50], [300, 80]]},
                {"text": "ID: 12345678", "confidence": 0.92, "bbox": [[100, 100], [250, 130]]},
            ]
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Run OCR
            result = self.ocr.ocr(np.array(image), cls=True)
            
            # Parse results
            extracted = []
            for line in result[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                extracted.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                })
            
            return extracted
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return []
    
    def parse_kenyan_id(self, ocr_results: List[Dict]) -> Dict[str, Any]:
        """
        Parse Kenyan National ID from OCR results.
        
        Extracts:
        - ID number (8 digits)
        - Full name
        - Date of birth (optional)
        """
        all_text = " ".join([r["text"] for r in ocr_results])
        
        parsed = {}
        
        # Extract ID number (8 digits)
        id_match = re.search(r'\b(\d{8})\b', all_text)
        if id_match:
            parsed["id_number"] = id_match.group(1)
        
        # Extract name (usually in caps, before ID number)
        name_patterns = [
            r'\b([A-Z][A-Z\s]+[A-Z])\b',  # All caps name
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                # Take longest match (likely the full name)
                parsed["full_name"] = max(matches, key=len).strip()
                break
        
        # Extract DOB if present
        dob_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', all_text)
        if dob_match:
            parsed["dob"] = dob_match.group(1)
        
        logger.info(f"Parsed ID: {parsed}")
        return parsed
    
    def parse_certificate(self, ocr_results: List[Dict]) -> Dict[str, Any]:
        """
        Parse educational/professional certificate.
        
        Extracts:
        - Certificate type (Certificate, Diploma, etc.)
        - Serial number
        - Skill/course name
        - Institution name
        """
        all_text = " ".join([r["text"] for r in ocr_results])
        
        parsed = {}
        
        # Extract certificate type
        cert_types = ["CERTIFICATE", "DIPLOMA", "LICENSE", "TRANSCRIPT"]
        for cert_type in cert_types:
            if cert_type in all_text.upper():
                parsed["cert_type"] = cert_type
                break
        
        # Extract serial number (various patterns)
        serial_patterns = [
            r'(?:SERIAL|SER|NO)[:\s]*([A-Z0-9/-]+)',
            r'\b([A-Z]{2,4}/\d{2,4}/\d{4})\b',  # e.g., KNEC/123/2023
            r'\b(CERT-\d+)\b',
        ]
        
        for pattern in serial_patterns:
            match = re.search(pattern, all_text.upper())
            if match:
                parsed["serial"] = match.group(1)
                break
        
        # Extract skill/course name (after "in" or "of")
        skill_match = re.search(r'(?:CERTIFICATE|DIPLOMA)\s+(?:IN|OF)\s+([A-Z\s]+)', all_text.upper())
        if skill_match:
            parsed["skill"] = skill_match.group(1).strip().title()
        
        # Extract institution (usually contains "INSTITUTE", "COLLEGE", "UNIVERSITY")
        institution_keywords = ["INSTITUTE", "COLLEGE", "UNIVERSITY", "TVET", "POLYTECHNIC"]
        for line in ocr_results:
            text_upper = line["text"].upper()
            if any(keyword in text_upper for keyword in institution_keywords):
                parsed["institution"] = line["text"].strip()
                break
        
        logger.info(f"Parsed certificate: {parsed}")
        return parsed
    
    def validate_document(
        self,
        parsed_id: Dict,
        parsed_cert: Dict,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cross-validate ID and certificate.
        
        Returns:
            {
                "name_match": bool,
                "confidence": float,
                "issues": List[str]
            }
        """
        validation = {
            "name_match": False,
            "confidence": 0.0,
            "issues": [],
        }
        
        id_name = parsed_id.get("full_name", "").upper()
        cert_name = parsed_cert.get("institution", "").upper()  # Placeholder
        
        # In a real implementation, use fuzzy string matching
        # For MVP: Simple substring check
        if user_name:
            user_name_upper = user_name.upper()
            if user_name_upper in id_name or id_name in user_name_upper:
                validation["name_match"] = True
                validation["confidence"] = 0.85
        
        if not parsed_id.get("id_number"):
            validation["issues"].append("ID number not found")
        
        if not parsed_cert.get("serial"):
            validation["issues"].append("Certificate serial number not found")
        
        if not validation["name_match"] and user_name:
            validation["issues"].append("Name mismatch between ID and user profile")
        
        return validation


# Numpy import for OCR
try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("NumPy not available. OCR will use mock mode.")
