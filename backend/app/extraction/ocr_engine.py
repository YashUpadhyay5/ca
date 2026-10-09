import fitz  # PyMuPDF
from typing import List, Tuple, Optional
import numpy as np
import io
from PIL import Image

class OCREngine:
    """Enterprise OCR Engine supporting ONNX-powered RapidOCR with image preprocessing."""

    _ocr_instance = None

    @classmethod
    def get_instance(cls):
        """Lazy loader for RapidOCR ONNX model."""
        if cls._ocr_instance is None:
            try:
                from rapidocr_onnxruntime import RapidOCR
                cls._ocr_instance = RapidOCR()
            except ImportError:
                cls._ocr_instance = None
        return cls._ocr_instance

    @classmethod
    def is_page_scanned(cls, page: fitz.Page) -> bool:
        """Determines if a page is scanned/image-based vs digital text."""
        text = page.get_text().strip()
        # If there are fewer than 30 characters extracted digitally, it is an image/scanned page
        return len(text) < 30

    @classmethod
    def ocr_page(cls, doc: fitz.Document, page_number: int) -> Tuple[List[List[str]], float]:
        """
        Renders PDF page to image, runs RapidOCR, and reconstructs 2D table grid.
        Returns: (reconstructed_table_rows, average_ocr_confidence)
        """
        ocr = cls.get_instance()
        if not ocr or page_number < 1 or page_number > len(doc):
            return [], 0.0

        page = doc[page_number - 1]
        # Render high-resolution pixmap (2.0 scale = ~150-200 DPI)
        matrix = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=matrix)
        img_bytes = pix.tobytes("png")
        
        # Load image via PIL into numpy array
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_np = np.array(img)

        result, elapse_list = ocr(img_np)
        if not result:
            return [], 0.0

        # Each result item: [dt_boxes, text, score]
        lines_dict = {}
        total_score = 0.0
        count = 0

        for box, text, score in result:
            total_score += float(score)
            count += 1
            # box is [[x0,y0], [x1,y1], [x2,y2], [x3,y3]]
            top_y = min(p[1] for p in box)
            left_x = min(p[0] for p in box)
            
            # Snap y to nearest ~15px line cluster
            line_key = round(top_y / 15.0) * 15.0
            if line_key not in lines_dict:
                lines_dict[line_key] = []
            lines_dict[line_key].append((left_x, text.strip()))

        avg_conf = (total_score / count) if count > 0 else 0.0

        # Build ordered 2D table
        table_rows = []
        for y in sorted(lines_dict.keys()):
            words_in_line = sorted(lines_dict[y], key=lambda x: x[0])
            line_cells = [w[1] for w in words_in_line if w[1]]
            if line_cells:
                table_rows.append(line_cells)

        return table_rows, avg_conf
