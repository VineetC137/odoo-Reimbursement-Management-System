"""
Tests for OCR API endpoints.
"""
import pytest
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_test_receipt_image():
    """Create a simple test receipt image with text."""
    # Create a white image
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text to simulate a receipt
    text_lines = [
        "Starbucks Coffee",
        "123 Main Street",
        "Date: 01/15/2024",
        "",
        "Coffee         $4.50",
        "Muffin         $3.25",
        "",
        "Total:        $7.75",
        "",
        "Thank you!"
    ]
    
    y_position = 50
    for line in text_lines:
        draw.text((50, y_position), line, fill='black')
        y_position += 40
    
    # Save to BytesIO
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


def test_parse_receipt_success(client):
    """Test successful receipt parsing."""
    # Create test image
    img_bytes = create_test_receipt_image()
    
    # Upload file
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "raw_text" in data
    assert "amount" in data
    assert "currency_guess" in data
    assert "date" in data
    assert "merchant" in data
    
    # Verify raw_text is not empty
    assert len(data["raw_text"]) > 0


def test_parse_receipt_png_format(client):
    """Test receipt parsing with PNG format."""
    # Create PNG image
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Test Receipt", fill='black')
    draw.text((50, 100), "Total: $25.00", fill='black')
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.png", img_bytes, "image/png")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "raw_text" in data


def test_parse_receipt_invalid_format(client):
    """Test that invalid file formats are rejected."""
    # Create a text file
    file_content = b"This is not an image"
    
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.txt", BytesIO(file_content), "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_parse_receipt_file_too_large(client):
    """Test that files exceeding size limit are rejected."""
    # Create a large file (11 MB)
    large_content = b"x" * (11 * 1024 * 1024)
    
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.jpg", BytesIO(large_content), "image/jpeg")}
    )
    
    assert response.status_code == 400
    assert "File size exceeds" in response.json()["detail"]


def test_parse_receipt_no_file(client):
    """Test that request without file is rejected."""
    response = client.post("/api/ocr/parse-receipt")
    
    assert response.status_code == 422  # Unprocessable Entity


def test_parse_receipt_jpeg_extension(client):
    """Test receipt parsing with .jpeg extension."""
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Store Name", fill='black')
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.jpeg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200


def test_parse_receipt_case_insensitive_extension(client):
    """Test that file extension validation is case-insensitive."""
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Test", fill='black')
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        "/api/ocr/parse-receipt",
        files={"file": ("receipt.JPG", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
