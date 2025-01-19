import logging
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
from typing import Dict

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Preprocesses images for OCR text extraction."""
    
    def __init__(self):
        """Initialize the image preprocessor."""
        logger.info("Initializing ImagePreprocessor")
        
    def process_image(self, image_bytes: bytes) -> str:
        """Process image and extract text."""
        try:
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Basic preprocessing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Thresholding
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save debug image
            cv2.imwrite('debug_processed.png', binary)
            
            # Extract text with improved configuration
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            text = pytesseract.image_to_string(binary, config=custom_config)
            
            logger.info(f"Extracted text: {text}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise ValueError("Failed to process image. Please ensure the image is clear and all text is visible.") 