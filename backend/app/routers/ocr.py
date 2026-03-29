from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas import ParsedReceipt
from app.services.ocr_service import OCRService
import tempfile
import os
from pathlib import Path

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/parse-receipt", response_model=ParsedReceipt)
async def parse_receipt(file: UploadFile = File(...)):
    """
    Parse a receipt image and extract text data using OCR.
    
    Accepts JPEG, PNG, or PDF files up to 10 MB.
    Returns extracted text with parsed amount, date, merchant, and currency guess.
    """
    # Validate file format
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024 * 1024)} MB"
        )
    
    # Create temporary file to store uploaded image
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Parse receipt using OCR service
        try:
            result = OCRService.parse_receipt(temp_file_path)
            return ParsedReceipt(**result)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process receipt: {str(e)}"
        )
