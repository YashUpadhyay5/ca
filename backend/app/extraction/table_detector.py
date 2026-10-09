import pdfplumber
import fitz  # PyMuPDF
import re
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

class TableDetector:
    """Detects and extracts 2D structured table grids from digital and OCR pages."""

    COLUMN_KEYWORDS = {
        "date": ["TRANSACTION DATE", "TXN DATE", "VALUE DATE", "POSTING DATE", "TRAN DATE", "DATE"],
        "narration": ["TRANSACTION REMARKS", "PARTICULARS", "DESCRIPTION", "NARRATION", "REMARKS", "DETAILS"],
        "chq": ["CHEQUE NUMBER", "CHQ NO", "REF NO", "CHEQUE", "CHQ", "REF.", "UTR"],
        "debit": ["WITHDRAWAL AMOUNT", "WITHDRAWAL", "DEBIT", "DR AMT", "DR.", "DR"],
        "credit": ["DEPOSIT AMOUNT", "DEPOSIT", "CREDIT", "CR AMT", "CR.", "CR"],
        "balance": ["BALANCE (INR)", "CLOSING BALANCE", "BALANCE", "BAL"],
        "s_no": ["S NO", "SL NO", "SR NO", "NO."]
    }

    _cached_bounds: Optional[List[Tuple[str, float, float]]] = None
    _cached_pdf_path: Optional[str] = None

    @classmethod
    def _find_header_band(cls, words: List[Dict[str, Any]]) -> Tuple[Optional[float], List[Dict[str, Any]]]:
        """Finds vertical window with maximum distinct banking table columns."""
        words_by_y = sorted([w for w in words if w['top'] < 350], key=lambda w: w['top'])
        best_score = 0
        best_words: List[Dict[str, Any]] = []

        for w in words_by_y:
            y_center = w['top']
            win_words = [cw for cw in words_by_y if y_center - 8 <= cw['top'] <= y_center + 18]
            matched_cats = set()
            for cw in win_words:
                t = cw['text'].upper()
                for cat, kws in cls.COLUMN_KEYWORDS.items():
                    if cat not in matched_cats:
                        for kw in kws:
                            if kw == t or t.startswith(kw) or (len(t) > 3 and kw in t):
                                matched_cats.add(cat)
                                break
            if len(matched_cats) > best_score:
                best_score = len(matched_cats)
                best_words = win_words

        if best_score >= 3:
            h_bottom = max(w['bottom'] for w in best_words) + 2
            return h_bottom, best_words
        return None, []

    @classmethod
    def _cluster_header_words(cls, header_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clusters header words by horizontal proximity into column bins."""
        sorted_words = sorted(header_words, key=lambda w: w['x0'])
        clusters: List[Dict[str, Any]] = []
        for w in sorted_words:
            if not clusters:
                clusters.append({'x0': w['x0'], 'x1': w['x1'], 'words': [w]})
            else:
                prev = clusters[-1]
                if w['x0'] <= prev['x1'] + 8:
                    prev['x1'] = max(prev['x1'], w['x1'])
                    prev['words'].append(w)
                else:
                    clusters.append({'x0': w['x0'], 'x1': w['x1'], 'words': [w]})

        for c in clusters:
            c['text'] = " ".join(w['text'] for w in sorted(c['words'], key=lambda x: (round(x['top'] / 3) * 3, x['x0'])))
        return clusters

    @classmethod
    def extract_stream_table_anchors(cls, pdf_path: str, page_number: int) -> List[List[str]]:
        """
        Universal Dynamic Stream & Anchor Table Extractor.
        Detects borderless transaction tables by computing column boundaries from header clusters
        and slicing rows using transaction date anchors. Handles multi-line narrations cleanly.
        """
        rows: List[List[str]] = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not (1 <= page_number <= len(pdf.pages)):
                    return rows

                if cls._cached_pdf_path != pdf_path:
                    cls._cached_bounds = None
                    cls._cached_pdf_path = pdf_path

                page = pdf.pages[page_number - 1]
                words = page.extract_words()
                if not words:
                    return rows

                col_bounds = cls._cached_bounds
                page_h_bottom, h_words = cls._find_header_band(words)

                if h_words and len(h_words) >= 3:
                    clusters = cls._cluster_header_words(h_words)
                    new_bounds = []
                    for i, c in enumerate(clusters):
                        txt = c['text'].upper()
                        if i == 0:
                            left = 0.0
                        else:
                            if any(k in txt for k in ["REMARK", "PARTICULAR", "DESC", "NARR"]):
                                left = clusters[i - 1]['x1'] + 2.0
                            elif any(k in txt for k in ["WITHDRAWAL", "DEBIT", "DR"]):
                                left = c['x0'] - 4.0
                            else:
                                left = (clusters[i - 1]['x1'] + c['x0']) / 2.0

                        if i == len(clusters) - 1:
                            right = float(page.width) + 100.0
                        else:
                            next_txt = clusters[i + 1]['text'].upper()
                            if any(k in next_txt for k in ["WITHDRAWAL", "DEBIT", "DR"]):
                                right = clusters[i + 1]['x0'] - 4.0
                            elif any(k in txt for k in ["CHQ", "CHEQUE"]):
                                right = c['x1'] + 2.0
                            else:
                                right = (c['x1'] + clusters[i + 1]['x0']) / 2.0

                        new_bounds.append((c['text'], left, right))
                    col_bounds = new_bounds
                    cls._cached_bounds = col_bounds

                if not col_bounds and page_number > 1:
                    p1_words = pdf.pages[0].extract_words()
                    _, p1_h_words = cls._find_header_band(p1_words)
                    if p1_h_words:
                        clusters = cls._cluster_header_words(p1_h_words)
                        new_bounds = []
                        for i, c in enumerate(clusters):
                            txt = c['text'].upper()
                            if i == 0:
                                left = 0.0
                            else:
                                if any(k in txt for k in ["REMARK", "PARTICULAR", "DESC", "NARR"]):
                                    left = clusters[i - 1]['x1'] + 2.0
                                elif any(k in txt for k in ["WITHDRAWAL", "DEBIT", "DR"]):
                                    left = c['x0'] - 4.0
                                else:
                                    left = (clusters[i - 1]['x1'] + c['x0']) / 2.0

                            if i == len(clusters) - 1:
                                right = float(page.width) + 100.0
                            else:
                                next_txt = clusters[i + 1]['text'].upper()
                                if any(k in next_txt for k in ["WITHDRAWAL", "DEBIT", "DR"]):
                                    right = clusters[i + 1]['x0'] - 4.0
                                elif any(k in txt for k in ["CHQ", "CHEQUE"]):
                                    right = c['x1'] + 2.0
                                else:
                                    right = (c['x1'] + clusters[i + 1]['x0']) / 2.0

                            new_bounds.append((c['text'], left, right))
                        col_bounds = new_bounds
                        cls._cached_bounds = col_bounds

                if not col_bounds:
                    return rows

                if page_h_bottom is None:
                    page_h_bottom = 105.0

                footer_top = float(page.height)
                for w in words:
                    if w['top'] > 280:
                        txt_lower = w['text'].lower()
                        if any(k in txt_lower for k in [
                            'sincerely', 'sincerly', 'legends', 'system generated',
                            'dial your bank', 'www.', 'page ', 'continued on', 'toll free'
                        ]):
                            footer_top = min(footer_top, w['top'])

                table_words = [w for w in words if page_h_bottom <= w['top'] < footer_top]

                date_bound = next((b for b in col_bounds if "DATE" in b[0].upper()), None)
                if not date_bound:
                    return rows

                _, d_left, d_right = date_bound

                date_anchors = [
                    w for w in table_words
                    if d_left <= w['x0'] <= d_right and re.match(
                        r"^(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}[- ][A-Za-z]{3}[- ]\d{2,4})$",
                        w['text']
                    )
                ]
                date_anchors.sort(key=lambda w: w['top'])

                if not date_anchors:
                    return rows

                header_row = [b[0] for b in col_bounds]
                rows.append(header_row)

                for i, dw in enumerate(date_anchors):
                    y_start = dw['top'] - 6.0
                    y_end = (date_anchors[i + 1]['top'] - 6.0) if i < len(date_anchors) - 1 else footer_top
                    row_words = [w for w in table_words if y_start <= w['top'] < y_end]

                    row_cells = [[] for _ in col_bounds]
                    for w in row_words:
                        x_mid = (w['x0'] + w['x1']) / 2.0
                        for c_idx, (_, left, right) in enumerate(col_bounds):
                            if left <= x_mid < right:
                                row_cells[c_idx].append(w)
                                break

                    row_vals = []
                    for c_idx, (col_name, _, _) in enumerate(col_bounds):
                        cell_w = row_cells[c_idx]
                        if any(k in col_name.upper() for k in ["REMARK", "PARTICULAR", "DESC", "NARR"]):
                            cell_w.sort(key=lambda x: (round(x['top'] / 4.0) * 4.0, x['x0']))
                        row_vals.append(" ".join(w['text'] for w in cell_w).strip())

                    rows.append(row_vals)

        except Exception:
            pass

        return rows

    @classmethod
    def extract_tables_pdfplumber(cls, pdf_path: str, page_number: int) -> List[List[List[str]]]:
        """
        Attempts lattice grid extraction first. If borderless or empty,
        seamlessly falls back to dynamic stream anchor table extraction.
        Returns a list of 2D tables [[row1_cols], [row2_cols], ...].
        """
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if 1 <= page_number <= len(pdf.pages):
                    page = pdf.pages[page_number - 1]

                    extracted = page.extract_tables({
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "snap_tolerance": 3,
                    })

                    if extracted:
                        for tbl in extracted:
                            cleaned_tbl = []
                            for row in tbl:
                                cleaned_row = [str(cell or "").strip() for cell in row]
                                if any(cleaned_row):
                                    cleaned_tbl.append(cleaned_row)
                            if len(cleaned_tbl) >= 3:
                                tables.append(cleaned_tbl)

            if not tables:
                stream_tbl = cls.extract_stream_table_anchors(pdf_path, page_number)
                if stream_tbl and len(stream_tbl) >= 2:
                    tables.append(stream_tbl)

        except Exception:
            pass

        return tables

    @classmethod
    def extract_text_pymupdf_fallback(cls, pdf_path: str, page_number: int) -> List[List[str]]:
        """
        High-performance PyMuPDF fallback: groups word blocks by Y-coordinate into table rows.
        """
        rows = []
        try:
            doc = fitz.open(pdf_path)
            if 0 <= (page_number - 1) < len(doc):
                page = doc[page_number - 1]
                words = page.get_text("words")
                doc.close()

                lines_dict = {}
                for w in words:
                    x0, y0, x1, y1, text, bno, lno, wno = w
                    line_key = round(y0 / 4.0) * 4.0
                    if line_key not in lines_dict:
                        lines_dict[line_key] = []
                    lines_dict[line_key].append((x0, text))

                sorted_y = sorted(lines_dict.keys())
                for y in sorted_y:
                    line_words = sorted(lines_dict[y], key=lambda item: item[0])
                    full_line_tokens = [w[1] for w in line_words]
                    if full_line_tokens:
                        rows.append(full_line_tokens)
        except Exception:
            pass

        return rows
