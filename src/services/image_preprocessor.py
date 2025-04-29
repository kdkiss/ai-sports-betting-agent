import logging
import easyocr
import cv2
import numpy as np
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Preprocesses images for OCR text extraction from bet slips using EasyOCR."""
    
    def __init__(self):
        """Initialize the image preprocessor with EasyOCR."""
        logger.info("Initializing ImagePreprocessor with EasyOCR")
        self.reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have a GPU

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for OCR."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            return blurred
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}", exc_info=True)
            raise

    def process_image(self, image_bytes: bytes) -> str:
        """Process image and extract text using EasyOCR."""
        try:
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image")
            
            # Upscale image for better text recognition
            scale_factor = 2.0
            image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
            
            # Preprocess the image
            processed = self.preprocess_image(image)
            
            # Save debug image
            debug_path = 'debug_processed.png'
            cv2.imwrite(debug_path, processed)
            logger.info(f"Saved processed image to {debug_path}")
            
            # Extract text with EasyOCR
            results = self.reader.readtext(processed, detail=0, paragraph=True)
            text = '\n'.join(results)
            
            # Clean and structure the text
            cleaned_text = self._clean_text(text)
            
            logger.info(f"Extracted text: {cleaned_text[:100]}...")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise ValueError(
                "Failed to process image. Please ensure the image is clear, well-lit, and contains readable text. "
                "Try increasing resolution, straightening the image, or removing background noise."
            )

    def _clean_text(self, text: str) -> str:
        """Clean and structure the OCR-extracted text."""
        try:
            # Split into lines and remove empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            
            # Merge fragmented lines (e.g., odds and amounts split across lines)
            cleaned_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Look for odds (e.g., +250, -110) or currency (e.g., $100)
                if re.search(r'[\+\-]\d+|\$\d+', line):
                    # Check if next line seems related (e.g., wager amount or team name)
                    if i + 1 < len(lines) and re.search(r'[\w\s]+|\$\d+', lines[i+1]):
                        line += " " + lines[i+1]
                        i += 1
                cleaned_lines.append(line)
                i += 1
            
            # Join lines with newlines
            cleaned_text = '\n'.join(cleaned_lines)
            
            # Remove excessive whitespace and invalid characters
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            cleaned_text = re.sub(r'[^\w\s\+\-\.\$\/():]', '', cleaned_text)
            
            return cleaned_text.strip()
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text.strip()