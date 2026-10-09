import os
from decimal import Decimal
from typing import List, Any, Optional, Dict
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.config import settings


class ExcelExportService:
    """
    Enterprise-Grade Multi-Sheet CA Financial Analysis Workbook Generator.
    Adheres strictly to ICAI audit documentation standards, producing 13 dedicated
    interlinked sheets with real Excel Tables, dynamic structured formulas, native
    date/currency formatting, and complete mathematical reconciliation.
    """

    # Brand Colors (Navy & Slate CA Corporate Palette)
    NAVY_HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    DARK_BLUE_FILL = PatternFill(start_color="172554", end_color="172554", fill_type="solid")
    SUB_HEADER_FILL = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    ACCENT_ROW_FILL = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    SUCCESS_FILL = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    ALERT_FILL = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    CARD_BG_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # Typography
    TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    SECTION_FONT = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    SUB_HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    DATA_FONT = Font(name="Calibri", size=10, color="0F172A")
    BOLD_DATA_FONT = Font(name="Calibri", size=10, bold=True, color="0F172A")
    MUTED_FONT = Font(name="Calibri", size=9, italic=True, color="64748B")
    KPI_VALUE_FONT = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    KPI_LABEL_FONT = Font(name="Calibri", size=9, bold=True, color="475569")
    SUCCESS_FONT = Font(name="Calibri", size=11, bold=True, color="166534")
    ALERT_FONT = Font(name="Calibri", size=11, bold=True, color="991B1B")

    # Borders
    THIN_BORDER = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    HEADER_BORDER = Border(
        left=Side(style='thin', color='3B82F6'),
        right=Side(style='thin', color='3B82F6'),
        top=Side(style='medium', color='1E3A8A'),
        bottom=Side(style='medium', color='1E3A8A')
    )
    TOTAL_ROW_BORDER = Border(
        top=Side(style='thin', color='0F172A'),
        bottom=Side(style='double', color='0F172A')
    )

    # Number Formats
    CURRENCY_FORMAT = '₹#,##0.00'
    NUMBER_FORMAT = '#,##0.00'
    INTEGER_FORMAT = '#,##0'
    PERCENT_FORMAT = '0.0%'
    DATE_FORMAT = 'dd-mmm-yyyy'

    @classmethod
    def _style_header_row(cls, ws, row_idx: int, fill=None, font=None):
        f = fill or cls.NAVY_HEADER_FILL
        ft = font or cls.HEADER_FONT
        for cell in ws[row_idx]:
            cell.fill = f
            cell.font = ft
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = cls.HEADER_BORDER

    @classmethod
    def _autofit_columns(cls, ws, min_width: int = 12, max_width: int = 50):
        ws.views.sheetView[0].showGridLines = True
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = cell.value
                if val is not None:
                    val_str = str(val)
                    if "\n" in val_str:
                        lines = val_str.split("\n")
                        max_len = max(max_len, max(len(l) for l in lines))
                    else:
                        max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, min_width), max_width)

    @classmethod
    def generate_statement_workbook(
        cls,
        statement: Any,
        transactions: List[Any],
        overview_metrics: dict,
        monthly_data: list,
        payment_modes: list,
        categories: list,
        reconciliation_report: dict,
        review_items: list,
        client_name: str = "Client Account"
    ) -> Path:
        """
        Generates production-grade 13-sheet CA working papers Excel workbook.
        """
        wb = Workbook()
        # Remove default active sheet
        wb.remove(wb.active)

        # -------------------------------------------------------------
        # SHEET 1: 01_Cover
        # -------------------------------------------------------------
        cls._build_cover_sheet(wb, statement, client_name, transactions)

        # -------------------------------------------------------------
        # SHEET 2: 02_Summary
        # -------------------------------------------------------------
        cls._build_summary_sheet(wb, statement, client_name)

        # -------------------------------------------------------------
        # SHEET 3: 03_Transactions (Master Table tblTransactions)
        # -------------------------------------------------------------
        cls._build_transactions_sheet(wb, transactions)

        # -------------------------------------------------------------
        # SHEET 4: 04_Above_10000 (Transferred more than 10,000)
        # -------------------------------------------------------------
        above_10k = [t for t in transactions if (getattr(t, 'debit_amount', 0) or 0) >= 10000 or (getattr(t, 'credit_amount', 0) or 0) >= 10000]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="04_Above_10000",
            heading_title="HIGH-VALUE TRANSACTIONS (EXCEEDING ₹10,000)",
            subtitle="Audit trail of high-value transactions >= ₹10,000 (ICAI Tax Audit Sec 40A(3), SFT & High-Value Clearing)",
            transactions=above_10k,
            table_name="tblAbove10K"
        )

        # -------------------------------------------------------------
        # SHEET 5: 05_Cash_Transactions (Cash & ATM)
        # -------------------------------------------------------------
        cash_txns = [t for t in transactions if (getattr(t, 'payment_mode', '') or '').upper() in ['ATM', 'CASH'] or any(k in (getattr(t, 'narration', '') or '').upper() for k in ['ATM', 'CASH', 'CDM', 'NFS', 'SELF', 'CWDR'])]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="05_Cash_Transactions",
            heading_title="CASH & ATM TRANSACTIONS (DEPOSITS & WITHDRAWALS)",
            subtitle="Complete ledger of cash deposits, cash withdrawals, ATM transactions, and self-cheque cash movements",
            transactions=cash_txns,
            table_name="tblCashTxns"
        )

        # -------------------------------------------------------------
        # SHEET 6: 06_Bank_Transfers_RTGS (RTGS / NEFT / IMPS / Net Banking)
        # -------------------------------------------------------------
        transfer_txns = [t for t in transactions if (getattr(t, 'payment_mode', '') or '').upper() in ['RTGS', 'NEFT', 'IMPS', 'TRANSFER'] or any(k in (getattr(t, 'narration', '') or '').upper() for k in ['RTGS', 'NEFT', 'IMPS', 'INFT', 'INF', 'MMT', 'NEFT/'])]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="06_Bank_Transfers_RTGS",
            heading_title="BANK TRANSFERS (RTGS / NEFT / IMPS / NET BANKING)",
            subtitle="Electronic inter-bank and intra-bank funds transfers, RTGS clearing, NEFT settlements, and IMPS payments",
            transactions=transfer_txns,
            table_name="tblTransfers"
        )

        # -------------------------------------------------------------
        # SHEET 7: 07_UPI_Transactions (UPI Payments & Receipts)
        # -------------------------------------------------------------
        upi_txns = [t for t in transactions if (getattr(t, 'payment_mode', '') or '').upper() == 'UPI' or 'UPI' in (getattr(t, 'narration', '') or '').upper()]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="07_UPI_Transactions",
            heading_title="UPI TRANSACTIONS (PAYMENTS & RECEIPTS)",
            subtitle="Complete ledger of Unified Payments Interface (UPI) consumer, merchant, and QR code transactions",
            transactions=upi_txns,
            table_name="tblUPITxns"
        )

        # -------------------------------------------------------------
        # SHEET 8: 08_Debit_Transactions (All Outflows / Expenses)
        # -------------------------------------------------------------
        debit_txns = [t for t in transactions if (getattr(t, 'debit_amount', 0) or 0) > 0]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="08_Debit_Transactions",
            heading_title="ALL DEBIT TRANSACTIONS (OUTFLOWS & EXPENSES)",
            subtitle="Complete ledger of all debit entries and payments with accounting subtotals",
            transactions=debit_txns,
            table_name="tblDebits"
        )

        # -------------------------------------------------------------
        # SHEET 9: 09_Credit_Transactions (All Inflows / Receipts)
        # -------------------------------------------------------------
        credit_txns = [t for t in transactions if (getattr(t, 'credit_amount', 0) or 0) > 0]
        cls._build_filtered_transaction_sheet(
            wb=wb,
            sheet_title="09_Credit_Transactions",
            heading_title="ALL CREDIT TRANSACTIONS (INFLOWS & RECEIPTS)",
            subtitle="Complete ledger of all credit entries, receipts, and deposits with accounting subtotals",
            transactions=credit_txns,
            table_name="tblCredits"
        )

        # -------------------------------------------------------------
        # SHEET 10: 10_Monthly_Analysis
        # -------------------------------------------------------------
        cls._build_monthly_analysis_sheet(wb, transactions, monthly_data)

        # -------------------------------------------------------------
        # SHEET 11: 11_Category_Analysis
        # -------------------------------------------------------------
        cls._build_category_analysis_sheet(wb, categories)

        # -------------------------------------------------------------
        # SHEET 12: 12_Reconciliation
        # -------------------------------------------------------------
        cls._build_reconciliation_sheet(wb, statement, reconciliation_report)

        # -------------------------------------------------------------
        # SHEET 13: 13_Reference_Data
        # -------------------------------------------------------------
        cls._build_reference_data_sheet(wb)

        # Save workbook to exports storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_acc = (statement.account_number_detected or "ACCT").replace("*", "X").replace(" ", "")
        file_name = f"Bank_Statement_Analysis_{safe_acc}_{timestamp}.xlsx"
        file_path = settings.EXPORTS_DIR / file_name

        # Ensure 03_Transactions is the active sheet when opening the workbook
        if "03_Transactions" in wb.sheetnames:
            wb.active = wb["03_Transactions"]

        wb.save(str(file_path))
        return file_path

    # =========================================================================
    # SHEET IMPLEMENTATIONS
    # =========================================================================

    @classmethod
    def _build_cover_sheet(cls, wb: Workbook, statement: Any, client_name: str, transactions: List[Any]):
        ws = wb.create_sheet(title="01_Cover")
        ws.views.sheetView[0].showGridLines = True

        # Document Header
        ws["B2"] = "BANK STATEMENT AUDIT WORKING PAPERS"
        ws["B2"].font = cls.TITLE_FONT
        ws["B3"] = "ICAI Compliant Audit Dossier & Automated Intelligence Summary"
        ws["B3"].font = cls.MUTED_FONT

        # Decorative Bar
        for col_idx in range(2, 6):
            cell = ws.cell(row=4, column=col_idx)
            cell.fill = cls.NAVY_HEADER_FILL
        ws.row_dimensions[4].height = 4

        # Metadata Table
        metadata = [
            ("Client / Taxpayer Name", client_name),
            ("Auditing CA Firm", "Chartered Accountant Practice & Associates"),
            ("Bank Name", statement.bank_name or "Detected Indian Bank"),
            ("Account Number (Masked)", statement.account_number_detected or "XXXXXX1234"),
            ("Statement Period", f"{statement.period_start or 'N/A'} to {statement.period_end or 'N/A'}"),
            ("Financial Year (Indian FY)", cls._get_financial_year(statement.period_start)),
            ("Statement Type", "Bank Current / Savings Account Statement"),
            ("Total Statement Pages", getattr(statement.document, 'page_count', 1) if statement.document else 1),
            ("Total Transactions Audited", len(transactions)),
            ("Extraction Engine", statement.parser_used or "Multi-Bank Parser Engine"),
            ("Overall Extraction Confidence", f"{float(statement.confidence_avg or 1.0) * 100:.1f}%"),
            ("Balance Invariant Reconciliation", statement.reconciliation_status or "RECONCILED"),
            ("Dossier Generation Date", datetime.now().strftime("%d-%b-%Y %H:%M:%S UTC")),
        ]

        start_row = 6
        for idx, (label, val) in enumerate(metadata):
            curr_row = start_row + idx
            ws.cell(row=curr_row, column=2, value=label).font = cls.BOLD_DATA_FONT
            ws.cell(row=curr_row, column=2).fill = cls.CARD_BG_FILL
            ws.cell(row=curr_row, column=2).border = cls.THIN_BORDER

            val_cell = ws.cell(row=curr_row, column=3, value=val)
            val_cell.font = cls.DATA_FONT
            val_cell.border = cls.THIN_BORDER

            # Special highlight for Reconciliation
            if label == "Balance Invariant Reconciliation":
                if val == "RECONCILED":
                    val_cell.fill = cls.SUCCESS_FILL
                    val_cell.font = cls.SUCCESS_FONT
                else:
                    val_cell.fill = cls.ALERT_FILL
                    val_cell.font = cls.ALERT_FONT

        # Audit Certification Sign-off Block
        sign_row = start_row + len(metadata) + 3
        ws.cell(row=sign_row, column=2, value="AUDIT ENGAGEMENT SIGN-OFF").font = cls.SECTION_FONT

        sign_fields = [
            ("Engagement Partner / CA:", "_______________________________"),
            ("ICAI Membership Number:", "_______________________________"),
            ("UDIN Reference (Optional):", "_______________________________"),
            ("Audit Sign-off Date:", datetime.now().strftime("%d-%b-%Y")),
        ]
        for s_idx, (f_lbl, f_val) in enumerate(sign_fields):
            r = sign_row + 2 + s_idx
            ws.cell(row=r, column=2, value=f_lbl).font = cls.BOLD_DATA_FONT
            ws.cell(row=r, column=3, value=f_val).font = cls.DATA_FONT

        cls._autofit_columns(ws, min_width=25)

    @classmethod
    def _build_summary_sheet(cls, wb: Workbook, statement: Any, client_name: str):
        ws = wb.create_sheet(title="02_Summary")
        ws.views.sheetView[0].showGridLines = True

        ws["B2"] = f"EXECUTIVE FINANCIAL SUMMARY - {client_name.upper()}"
        ws["B2"].font = cls.SECTION_FONT
        ws["B3"] = f"Account: {statement.account_number_detected or 'N/A'} | Bank: {statement.bank_name or 'N/A'}"
        ws["B3"].font = cls.MUTED_FONT

        # Section 1: Balances & Movement
        ws["B5"] = "1. STATEMENT BALANCES & NET MOVEMENT"
        ws["B5"].font = cls.BOLD_DATA_FONT
        ws["B5"].fill = cls.SUB_HEADER_FILL

        ws.cell(row=6, column=2, value="Metric").font = cls.HEADER_FONT
        ws.cell(row=6, column=2).fill = cls.NAVY_HEADER_FILL
        ws.cell(row=6, column=3, value="Amount (₹)").font = cls.HEADER_FONT
        ws.cell(row=6, column=3).fill = cls.NAVY_HEADER_FILL
        ws.cell(row=6, column=4, value="Calculation / Traceability Source").font = cls.HEADER_FONT
        ws.cell(row=6, column=4).fill = cls.NAVY_HEADER_FILL

        ws.cell(row=7, column=2, value="Opening Balance").font = cls.DATA_FONT
        ws.cell(row=7, column=3, value=float(statement.opening_balance or 0.0)).number_format = cls.CURRENCY_FORMAT
        ws.cell(row=7, column=4, value="Extracted from Statement Header / First Transaction").font = cls.MUTED_FONT

        ws.cell(row=8, column=2, value="Total Credits (Inflows)").font = cls.DATA_FONT
        ws.cell(row=8, column=3, value="=SUM(tblTransactions[Credit])").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=8, column=4, value="Structured formula: SUM(tblTransactions[Credit])").font = cls.MUTED_FONT

        ws.cell(row=9, column=2, value="Total Debits (Outflows)").font = cls.DATA_FONT
        ws.cell(row=9, column=3, value="=SUM(tblTransactions[Debit])").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=9, column=4, value="Structured formula: SUM(tblTransactions[Debit])").font = cls.MUTED_FONT

        ws.cell(row=10, column=2, value="Net Cash Flow").font = cls.BOLD_DATA_FONT
        ws.cell(row=10, column=3, value="=C8-C9").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=10, column=3).font = cls.BOLD_DATA_FONT
        ws.cell(row=10, column=4, value="Formula: Total Credits - Total Debits").font = cls.MUTED_FONT

        ws.cell(row=11, column=2, value="Calculated Closing Balance").font = cls.BOLD_DATA_FONT
        ws.cell(row=11, column=3, value="=C7+C8-C9").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=11, column=3).font = cls.BOLD_DATA_FONT
        ws.cell(row=11, column=4, value="Formula: Opening Balance + Credits - Debits").font = cls.MUTED_FONT

        ws.cell(row=12, column=2, value="Stated Closing Balance").font = cls.DATA_FONT
        ws.cell(row=12, column=3, value=float(statement.closing_balance or 0.0)).number_format = cls.CURRENCY_FORMAT
        ws.cell(row=12, column=4, value="Extracted from Statement Summary").font = cls.MUTED_FONT

        ws.cell(row=13, column=2, value="Reconciliation Discrepancy").font = cls.BOLD_DATA_FONT
        ws.cell(row=13, column=3, value="=C11-C12").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=13, column=3).font = cls.BOLD_DATA_FONT
        ws.cell(row=13, column=4, value="Formula: Calculated Closing - Stated Closing").font = cls.MUTED_FONT

        for r in range(7, 14):
            for c in range(2, 5):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Section 2: Volume & Statistical Indicators
        ws["B16"] = "2. TRANSACTION VOLUME & STATISTICAL INDICATORS"
        ws["B16"].font = cls.BOLD_DATA_FONT
        ws["B16"].fill = cls.SUB_HEADER_FILL

        ws.cell(row=17, column=2, value="Statistical Metric").font = cls.HEADER_FONT
        ws.cell(row=17, column=2).fill = cls.NAVY_HEADER_FILL
        ws.cell(row=17, column=3, value="Value").font = cls.HEADER_FONT
        ws.cell(row=17, column=3).fill = cls.NAVY_HEADER_FILL
        ws.cell(row=17, column=4, value="Excel Formula").font = cls.HEADER_FONT
        ws.cell(row=17, column=4).fill = cls.NAVY_HEADER_FILL

        stats_rows = [
            ("Total Transactions Count", "=COUNTA(tblTransactions[Transaction ID])", cls.INTEGER_FORMAT, "=COUNTA(tblTransactions[Transaction ID])"),
            ("Debit Transactions Count", '=COUNTIF(tblTransactions[Transaction Type],"DEBIT")', cls.INTEGER_FORMAT, '=COUNTIF(tblTransactions[Transaction Type],"DEBIT")'),
            ("Credit Transactions Count", '=COUNTIF(tblTransactions[Transaction Type],"CREDIT")', cls.INTEGER_FORMAT, '=COUNTIF(tblTransactions[Transaction Type],"CREDIT")'),
            ("Average Debit Outflow", "=AVERAGE(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=AVERAGE(tblTransactions[Debit])"),
            ("Average Credit Inflow", "=AVERAGE(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "=AVERAGE(tblTransactions[Credit])"),
            ("Median Debit Outflow", "=MEDIAN(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=MEDIAN(tblTransactions[Debit])"),
            ("Largest Debit Outflow", "=MAX(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=MAX(tblTransactions[Debit])"),
            ("Largest Credit Inflow", "=MAX(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "=MAX(tblTransactions[Credit])"),
            ("Smallest Debit (Non-Zero)", '=MINIFS(tblTransactions[Debit],tblTransactions[Debit],">0")', cls.CURRENCY_FORMAT, '=MINIFS(tblTransactions[Debit],tblTransactions[Debit],">0")'),
            ("Smallest Credit (Non-Zero)", '=MINIFS(tblTransactions[Credit],tblTransactions[Credit],">0")', cls.CURRENCY_FORMAT, '=MINIFS(tblTransactions[Credit],tblTransactions[Credit],">0")'),
        ]

        for s_idx, (m_label, formula_val, num_fmt, formula_desc) in enumerate(stats_rows):
            r = 18 + s_idx
            ws.cell(row=r, column=2, value=m_label).font = cls.DATA_FONT
            v_cell = ws.cell(row=r, column=3, value=formula_val)
            v_cell.font = cls.BOLD_DATA_FONT
            v_cell.number_format = num_fmt
            ws.cell(row=r, column=4, value=formula_desc).font = cls.MUTED_FONT

            for c in range(2, 5):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        cls._autofit_columns(ws, min_width=24)

    @classmethod
    def _build_transactions_sheet(cls, wb: Workbook, transactions: List[Any]):
        ws = wb.create_sheet(title="03_Transactions")
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "C2"

        columns = [
            "Transaction ID",
            "Transaction Date",
            "Value Date",
            "Narration",
            "Reference Number",
            "Cheque Number",
            "Debit",
            "Credit",
            "Balance",
            "Payment Mode",
            "Transaction Type",
            "Category",
            "Subcategory",
            "Counterparty",
            "UPI ID",
            "Source Page",
            "Confidence",
            "Validation Status",
            "Review Status",
            "Notes"
        ]

        ws.append(columns)
        cls._style_header_row(ws, 1)

        start_row = 2
        for idx, t in enumerate(transactions):
            txn_id = getattr(t, 'id', f"TXN_{idx+1:05d}")
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            v_date = t.value_date if isinstance(t.value_date, (date, datetime)) else (
                datetime.strptime(str(t.value_date), "%Y-%m-%d").date() if t.value_date else t_date
            )

            dr = float(t.debit_amount) if t.debit_amount else 0.0
            cr = float(t.credit_amount) if t.credit_amount else 0.0
            bal = float(t.balance) if t.balance is not None else 0.0
            conf = float(t.confidence_score) if t.confidence_score is not None else 1.0
            txn_type = "DEBIT" if dr > 0 else ("CREDIT" if cr > 0 else "ZERO")

            row_data = [
                idx + 1,
                t_date,
                v_date,
                t.narration or "",
                t.reference_number or "",
                t.cheque_number or "",
                dr,
                cr,
                bal,
                t.payment_mode or "TRANSFER",
                txn_type,
                t.category or "Miscellaneous",
                t.subcategory or "",
                t.counterparty or "",
                t.upi_id or "",
                t.source_page or 1,
                conf,
                t.validation_status or "VALIDATED",
                "PENDING" if getattr(t, 'validation_status', '') == "REVIEW_REQUIRED" else "VERIFIED",
                t.notes or ""
            ]
            ws.append(row_data)

        end_row = start_row + len(transactions) - 1
        if end_row < start_row:
            end_row = start_row  # Guard for empty statement

        # Format Columns
        for r in range(start_row, end_row + 1):
            # Dates
            ws.cell(row=r, column=2).number_format = cls.DATE_FORMAT
            ws.cell(row=r, column=2).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=3).number_format = cls.DATE_FORMAT
            ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")

            # Currency
            ws.cell(row=r, column=7).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r, column=8).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r, column=9).number_format = cls.CURRENCY_FORMAT

            # Confidence
            ws.cell(row=r, column=17).number_format = cls.PERCENT_FORMAT
            ws.cell(row=r, column=17).alignment = Alignment(horizontal="right")

            # Alignments
            ws.cell(row=r, column=1).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=10).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=11).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=16).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=18).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=19).alignment = Alignment(horizontal="center")

            for c in range(1, len(columns) + 1):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Register official Excel Table tblTransactions
        last_col_letter = get_column_letter(len(columns))
        table_ref = f"A1:{last_col_letter}{max(end_row, 2)}"
        tab = Table(displayName="tblTransactions", ref=table_ref)
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )
        tab.tableStyleInfo = style
        ws.add_table(tab)

        cls._autofit_columns(ws, min_width=12, max_width=45)

    @classmethod
    def _build_filtered_transaction_sheet(
        cls,
        wb: Workbook,
        sheet_title: str,
        heading_title: str,
        subtitle: str,
        transactions: List[Any],
        table_name: str
    ):
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "C5"

        ws["A1"] = heading_title
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = subtitle
        ws["A2"].font = cls.MUTED_FONT

        columns = [
            "S.No",
            "Transaction Date",
            "Value Date",
            "Narration / Description",
            "Cheque / Ref No",
            "Withdrawal (Debit)",
            "Deposit (Credit)",
            "Running Balance",
            "Payment Mode",
            "Category"
        ]

        start_row = 4
        for c_idx, col_name in enumerate(columns, start=1):
            ws.cell(row=start_row, column=c_idx, value=col_name)
        cls._style_header_row(ws, start_row)

        if not transactions:
            empty_row = start_row + 1
            ws.cell(row=empty_row, column=1, value="—").alignment = Alignment(horizontal="center")
            ws.cell(row=empty_row, column=4, value="No transactions found matching this category in this statement").font = cls.MUTED_FONT
            for col_i in range(1, len(columns) + 1):
                ws.cell(row=empty_row, column=col_i).border = cls.THIN_BORDER
            cls._autofit_columns(ws, min_width=12, max_width=45)
            return

        for idx, t in enumerate(transactions, start=1):
            r = start_row + idx
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            v_date = t.value_date if isinstance(t.value_date, (date, datetime)) else (
                datetime.strptime(str(t.value_date), "%Y-%m-%d").date() if t.value_date else t_date
            )
            dr_val = float(t.debit_amount) if (t.debit_amount is not None and Decimal(str(t.debit_amount)) > 0) else None
            cr_val = float(t.credit_amount) if (t.credit_amount is not None and Decimal(str(t.credit_amount)) > 0) else None
            bal_val = float(t.balance) if t.balance is not None else None
            ref_no = t.reference_number or t.cheque_number or ""

            ws.cell(row=r, column=1, value=idx).alignment = Alignment(horizontal="center")
            c_td = ws.cell(row=r, column=2, value=t_date)
            c_td.number_format = cls.DATE_FORMAT
            c_td.alignment = Alignment(horizontal="center")

            c_vd = ws.cell(row=r, column=3, value=v_date)
            c_vd.number_format = cls.DATE_FORMAT
            c_vd.alignment = Alignment(horizontal="center")

            c_narr = ws.cell(row=r, column=4, value=t.narration or "")
            c_narr.alignment = Alignment(wrap_text=True)

            ws.cell(row=r, column=5, value=ref_no).alignment = Alignment(horizontal="center")

            c_dr = ws.cell(row=r, column=6, value=dr_val)
            c_dr.number_format = cls.CURRENCY_FORMAT

            c_cr = ws.cell(row=r, column=7, value=cr_val)
            c_cr.number_format = cls.CURRENCY_FORMAT

            c_bal = ws.cell(row=r, column=8, value=bal_val)
            c_bal.number_format = cls.CURRENCY_FORMAT

            ws.cell(row=r, column=9, value=t.payment_mode or "OTHER").alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=10, value=t.category or "Miscellaneous").alignment = Alignment(horizontal="center")

            for col_i in range(1, len(columns) + 1):
                ws.cell(row=r, column=col_i).border = cls.THIN_BORDER

        end_row = start_row + len(transactions)

        # Register Excel Table
        last_col = get_column_letter(len(columns))
        table_ref = f"A{start_row}:{last_col}{end_row}"
        tab = Table(displayName=table_name, ref=table_ref)
        tab.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )
        ws.add_table(tab)

        # Add Subtotal / Accounting Total Row
        tot_row = end_row + 2
        ws.cell(row=tot_row, column=4, value="SUBTOTAL / TOTAL MOVEMENT").font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=4).alignment = Alignment(horizontal="right")
        dr_sub = ws.cell(row=tot_row, column=6, value=f"=SUBTOTAL(109,F{start_row+1}:F{end_row})")
        dr_sub.font = cls.BOLD_DATA_FONT
        dr_sub.number_format = cls.CURRENCY_FORMAT

        cr_sub = ws.cell(row=tot_row, column=7, value=f"=SUBTOTAL(109,G{start_row+1}:G{end_row})")
        cr_sub.font = cls.BOLD_DATA_FONT
        cr_sub.number_format = cls.CURRENCY_FORMAT

        for col_i in range(1, len(columns) + 1):
            ws.cell(row=tot_row, column=col_i).border = cls.TOTAL_ROW_BORDER

        cls._autofit_columns(ws, min_width=12, max_width=45)

    @classmethod
    def _build_monthly_analysis_sheet(cls, wb: Workbook, transactions: List[Any], monthly_data: list):
        ws = wb.create_sheet(title="10_Monthly_Analysis")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "MONTHLY CASH FLOW & RECONCILIATION ANALYSIS"
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = "Dynamic aggregation via Excel SUMIFS and COUNTIFS referencing tblTransactions"
        ws["A2"].font = cls.MUTED_FONT

        headers = [
            "Month Name", "Year", "Month No", "Debit Count", "Total Debit (₹)",
            "Credit Count", "Total Credit (₹)", "Net Cash Flow (₹)", "Average Debit (₹)", "Average Credit (₹)"
        ]

        start_row = 4
        ws.append(headers)
        cls._style_header_row(ws, start_row)

        # Collect unique year-months from transactions
        ym_set = set()
        for t in transactions:
            if t.transaction_date:
                dt = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                    datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date()
                )
                ym_set.add((dt.year, dt.month))

        sorted_ym = sorted(list(ym_set)) if ym_set else [(datetime.now().year, 4)]
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        row_cursor = start_row + 1
        for yr, mo in sorted_ym:
            m_label = f"{month_names[mo]} {yr}"
            # Excel date boundary formulas for the month
            # Date start: DATE(yr, mo, 1)
            # Date end: EOMONTH(DATE(yr, mo, 1), 0)
            d_start_expr = f"DATE({yr},{mo},1)"
            d_end_expr = f"EOMONTH(DATE({yr},{mo},1),0)"

            dr_count_formula = f'=COUNTIFS(tblTransactions[Transaction Date],">="&{d_start_expr},tblTransactions[Transaction Date],"<="&{d_end_expr},tblTransactions[Transaction Type],"DEBIT")'
            dr_sum_formula = f'=SUMIFS(tblTransactions[Debit],tblTransactions[Transaction Date],">="&{d_start_expr},tblTransactions[Transaction Date],"<="&{d_end_expr})'
            cr_count_formula = f'=COUNTIFS(tblTransactions[Transaction Date],">="&{d_start_expr},tblTransactions[Transaction Date],"<="&{d_end_expr},tblTransactions[Transaction Type],"CREDIT")'
            cr_sum_formula = f'=SUMIFS(tblTransactions[Credit],tblTransactions[Transaction Date],">="&{d_start_expr},tblTransactions[Transaction Date],"<="&{d_end_expr})'
            net_formula = f"=G{row_cursor}-E{row_cursor}"
            avg_dr_formula = f'=IF(D{row_cursor}>0,E{row_cursor}/D{row_cursor},0)'
            avg_cr_formula = f'=IF(F{row_cursor}>0,G{row_cursor}/F{row_cursor},0)'

            ws.append([
                m_label,
                yr,
                mo,
                dr_count_formula,
                dr_sum_formula,
                cr_count_formula,
                cr_sum_formula,
                net_formula,
                avg_dr_formula,
                avg_cr_formula
            ])

            # Formatting
            ws.cell(row=row_cursor, column=1).font = cls.BOLD_DATA_FONT
            ws.cell(row=row_cursor, column=2).alignment = Alignment(horizontal="center")
            ws.cell(row=row_cursor, column=3).alignment = Alignment(horizontal="center")
            ws.cell(row=row_cursor, column=4).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=5).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=6).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=7).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=8).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=8).font = cls.BOLD_DATA_FONT
            ws.cell(row=row_cursor, column=9).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=10).number_format = cls.CURRENCY_FORMAT

            for c in range(1, 11):
                ws.cell(row=row_cursor, column=c).border = cls.THIN_BORDER

            row_cursor += 1

        # Summary Total Row
        tot_row = row_cursor
        ws.cell(row=tot_row, column=1, value="TOTAL / SUMMARY").font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=4, value=f"=SUM(D{start_row+1}:D{tot_row-1})").number_format = cls.INTEGER_FORMAT
        ws.cell(row=tot_row, column=4).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=5, value=f"=SUM(E{start_row+1}:E{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=5).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=6, value=f"=SUM(F{start_row+1}:F{tot_row-1})").number_format = cls.INTEGER_FORMAT
        ws.cell(row=tot_row, column=6).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=7, value=f"=SUM(G{start_row+1}:G{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=7).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=8, value=f"=SUM(H{start_row+1}:H{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=8).font = cls.BOLD_DATA_FONT

        for c in range(1, 11):
            ws.cell(row=tot_row, column=c).border = cls.TOTAL_ROW_BORDER

        cls._autofit_columns(ws, min_width=14)

    @classmethod
    def _build_debit_analysis_sheet(cls, wb: Workbook, transactions: List[Any]):
        ws = wb.create_sheet(title="05_Debit_Analysis")
        ws.views.sheetView[0].showGridLines = True

        ws["B2"] = "COMPREHENSIVE DEBIT & OUTFLOW ANALYSIS"
        ws["B2"].font = cls.SECTION_FONT

        # KPI Summary Table
        ws["B4"] = "DEBIT INDICATOR"
        ws["B4"].font = cls.HEADER_FONT
        ws["B4"].fill = cls.NAVY_HEADER_FILL
        ws["C4"] = "METRIC VALUE"
        ws["C4"].font = cls.HEADER_FONT
        ws["C4"].fill = cls.NAVY_HEADER_FILL
        ws["D4"] = "FORMULA / BENCHMARK"
        ws["D4"].font = cls.HEADER_FONT
        ws["D4"].fill = cls.NAVY_HEADER_FILL

        debit_kpis = [
            ("Total Debit Outflows", "=SUM(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=SUM(tblTransactions[Debit])"),
            ("Debit Transactions Count", '=COUNTIF(tblTransactions[Transaction Type],"DEBIT")', cls.INTEGER_FORMAT, '=COUNTIF(tblTransactions[Transaction Type],"DEBIT")'),
            ("Average Debit Outflow", "=AVERAGE(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=AVERAGE(tblTransactions[Debit])"),
            ("Largest Single Debit", "=MAX(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "=MAX(tblTransactions[Debit])"),
            ("Smallest Debit Outflow", '=MINIFS(tblTransactions[Debit],tblTransactions[Debit],">0")', cls.CURRENCY_FORMAT, '=MINIFS(tblTransactions[Debit],tblTransactions[Debit],">0")'),
            ("High-Value Debits (> ₹50,000) Count", '=COUNTIF(tblTransactions[Debit],">"&Reference_Data!B4)', cls.INTEGER_FORMAT, 'Threshold from Reference_Data!B4'),
            ("High-Value Debits Total Sum", '=SUMIF(tblTransactions[Debit],">"&Reference_Data!B4)', cls.CURRENCY_FORMAT, 'Threshold from Reference_Data!B4'),
        ]

        for idx, (label, formula, fmt, desc) in enumerate(debit_kpis):
            r = 5 + idx
            ws.cell(row=r, column=2, value=label).font = cls.DATA_FONT
            v_cell = ws.cell(row=r, column=3, value=formula)
            v_cell.font = cls.BOLD_DATA_FONT
            v_cell.number_format = fmt
            ws.cell(row=r, column=4, value=desc).font = cls.MUTED_FONT
            for c in range(2, 5):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Top 15 Outflows Table
        top_hdr_row = 14
        ws.cell(row=top_hdr_row - 1, column=2, value="TOP 15 DEBIT TRANSACTIONS AUDIT TRAIL").font = cls.SECTION_FONT

        table_headers = ["Rank", "Date", "Narration", "Amount (₹)", "Payment Mode", "Category", "Reference Number"]
        for c_idx, h in enumerate(table_headers):
            cell = ws.cell(row=top_hdr_row, column=c_idx + 2, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.NAVY_HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.HEADER_BORDER

        # Filter and sort debits
        debits = [t for t in transactions if Decimal(str(t.debit_amount or 0)) > 0]
        sorted_dr = sorted(debits, key=lambda x: Decimal(str(x.debit_amount)), reverse=True)[:15]

        for idx, t in enumerate(sorted_dr):
            r = top_hdr_row + 1 + idx
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            ws.cell(row=r, column=2, value=idx + 1).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=3, value=t_date).number_format = cls.DATE_FORMAT
            ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=4, value=t.narration)
            ws.cell(row=r, column=5, value=float(t.debit_amount)).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r, column=5).font = cls.BOLD_DATA_FONT
            ws.cell(row=r, column=6, value=t.payment_mode or "TRANSFER").alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=7, value=t.category or "Miscellaneous")
            ws.cell(row=r, column=8, value=t.reference_number or "")

            for c in range(2, 9):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        cls._autofit_columns(ws, min_width=15)

    @classmethod
    def _build_credit_analysis_sheet(cls, wb: Workbook, transactions: List[Any]):
        ws = wb.create_sheet(title="06_Credit_Analysis")
        ws.views.sheetView[0].showGridLines = True

        ws["B2"] = "COMPREHENSIVE CREDIT & INFLOW ANALYSIS"
        ws["B2"].font = cls.SECTION_FONT

        # KPI Summary Table
        ws["B4"] = "CREDIT INDICATOR"
        ws["B4"].font = cls.HEADER_FONT
        ws["B4"].fill = cls.NAVY_HEADER_FILL
        ws["C4"] = "METRIC VALUE"
        ws["C4"].font = cls.HEADER_FONT
        ws["C4"].fill = cls.NAVY_HEADER_FILL
        ws["D4"] = "FORMULA / BENCHMARK"
        ws["D4"].font = cls.HEADER_FONT
        ws["D4"].fill = cls.NAVY_HEADER_FILL

        credit_kpis = [
            ("Total Credit Inflows", "=SUM(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "=SUM(tblTransactions[Credit])"),
            ("Credit Transactions Count", '=COUNTIF(tblTransactions[Transaction Type],"CREDIT")', cls.INTEGER_FORMAT, '=COUNTIF(tblTransactions[Transaction Type],"CREDIT")'),
            ("Average Credit Inflow", "=AVERAGE(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "=AVERAGE(tblTransactions[Credit])"),
            ("Largest Single Credit", "=MAX(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "=MAX(tblTransactions[Credit])"),
            ("Smallest Credit Inflow", '=MINIFS(tblTransactions[Credit],tblTransactions[Credit],">0")', cls.CURRENCY_FORMAT, '=MINIFS(tblTransactions[Credit],tblTransactions[Credit],">0")'),
            ("High-Value Credits (> ₹50,000) Count", '=COUNTIF(tblTransactions[Credit],">"&Reference_Data!B4)', cls.INTEGER_FORMAT, 'Threshold from Reference_Data!B4'),
            ("High-Value Credits Total Sum", '=SUMIF(tblTransactions[Credit],">"&Reference_Data!B4)', cls.CURRENCY_FORMAT, 'Threshold from Reference_Data!B4'),
        ]

        for idx, (label, formula, fmt, desc) in enumerate(credit_kpis):
            r = 5 + idx
            ws.cell(row=r, column=2, value=label).font = cls.DATA_FONT
            v_cell = ws.cell(row=r, column=3, value=formula)
            v_cell.font = cls.BOLD_DATA_FONT
            v_cell.number_format = fmt
            ws.cell(row=r, column=4, value=desc).font = cls.MUTED_FONT
            for c in range(2, 5):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Top 15 Inflows Table
        top_hdr_row = 14
        ws.cell(row=top_hdr_row - 1, column=2, value="TOP 15 CREDIT INFLOWS AUDIT TRAIL").font = cls.SECTION_FONT

        table_headers = ["Rank", "Date", "Narration", "Amount (₹)", "Payment Mode", "Category", "Reference Number"]
        for c_idx, h in enumerate(table_headers):
            cell = ws.cell(row=top_hdr_row, column=c_idx + 2, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.NAVY_HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.HEADER_BORDER

        # Filter and sort credits
        credits = [t for t in transactions if Decimal(str(t.credit_amount or 0)) > 0]
        sorted_cr = sorted(credits, key=lambda x: Decimal(str(x.credit_amount)), reverse=True)[:15]

        for idx, t in enumerate(sorted_cr):
            r = top_hdr_row + 1 + idx
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            ws.cell(row=r, column=2, value=idx + 1).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=3, value=t_date).number_format = cls.DATE_FORMAT
            ws.cell(row=r, column=3).alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=4, value=t.narration)
            ws.cell(row=r, column=5, value=float(t.credit_amount)).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r, column=5).font = cls.BOLD_DATA_FONT
            ws.cell(row=r, column=6, value=t.payment_mode or "TRANSFER").alignment = Alignment(horizontal="center")
            ws.cell(row=r, column=7, value=t.category or "Miscellaneous")
            ws.cell(row=r, column=8, value=t.reference_number or "")

            for c in range(2, 9):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        cls._autofit_columns(ws, min_width=15)

    @classmethod
    def _build_payment_mode_sheet(cls, wb: Workbook, payment_modes: list):
        ws = wb.create_sheet(title="07_Payment_Mode")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "PAYMENT CHANNEL & MODE BREAKDOWN"
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = "Reconciles transactions across UPI, NEFT, RTGS, IMPS, Cheques, Cash & Digital Channels"
        ws["A2"].font = cls.MUTED_FONT

        headers = [
            "Payment Mode",
            "Transaction Count",
            "Total Debit (₹)",
            "Total Credit (₹)",
            "Net Movement (₹)",
            "Volume Share (%)"
        ]

        start_row = 4
        ws.append(headers)
        cls._style_header_row(ws, start_row)

        modes = ["UPI", "NEFT", "RTGS", "IMPS", "CHEQUE", "CASH", "CARD", "NETBANKING", "CHARGES", "TRANSFER", "OTHERS"]

        row_cursor = start_row + 1
        for mode in modes:
            count_f = f'=COUNTIF(tblTransactions[Payment Mode],"{mode}")'
            dr_f = f'=SUMIFS(tblTransactions[Debit],tblTransactions[Payment Mode],"{mode}")'
            cr_f = f'=SUMIFS(tblTransactions[Credit],tblTransactions[Payment Mode],"{mode}")'
            net_f = f"=D{row_cursor}-C{row_cursor}"
            share_f = f"=B{row_cursor}/COUNTA(tblTransactions[Transaction ID])"

            ws.append([mode, count_f, dr_f, cr_f, net_f, share_f])

            ws.cell(row=row_cursor, column=1).font = cls.BOLD_DATA_FONT
            ws.cell(row=row_cursor, column=1).alignment = Alignment(horizontal="center")
            ws.cell(row=row_cursor, column=2).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=3).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=4).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=5).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=5).font = cls.BOLD_DATA_FONT
            ws.cell(row=row_cursor, column=6).number_format = cls.PERCENT_FORMAT

            for c in range(1, 7):
                ws.cell(row=row_cursor, column=c).border = cls.THIN_BORDER

            row_cursor += 1

        # Total Row
        tot_row = row_cursor
        ws.cell(row=tot_row, column=1, value="TOTAL").font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=tot_row, column=2, value=f"=SUM(B{start_row+1}:B{tot_row-1})").number_format = cls.INTEGER_FORMAT
        ws.cell(row=tot_row, column=2).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=3, value=f"=SUM(C{start_row+1}:C{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=3).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=4, value=f"=SUM(D{start_row+1}:D{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=4).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=5, value=f"=SUM(E{start_row+1}:E{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=5).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=6, value=f"=SUM(F{start_row+1}:F{tot_row-1})").number_format = cls.PERCENT_FORMAT
        ws.cell(row=tot_row, column=6).font = cls.BOLD_DATA_FONT

        for c in range(1, 7):
            ws.cell(row=tot_row, column=c).border = cls.TOTAL_ROW_BORDER

        cls._autofit_columns(ws, min_width=16)

    @classmethod
    def _build_category_analysis_sheet(cls, wb: Workbook, categories: list):
        ws = wb.create_sheet(title="11_Category_Analysis")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "ACCOUNTING HEAD & CATEGORY AUDIT ANALYSIS"
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = "Categorization across Salaries, Taxes, Vendors, Rent, Remuneration & Utilities"
        ws["A2"].font = cls.MUTED_FONT

        headers = [
            "Category",
            "Debit Count",
            "Total Debit (₹)",
            "Credit Count",
            "Total Credit (₹)",
            "Net Movement (₹)"
        ]

        start_row = 4
        ws.append(headers)
        cls._style_header_row(ws, start_row)

        category_heads = [
            "Salary",
            "Rent",
            "Tax",
            "Vendor Payment",
            "Utilities",
            "Professional Fees",
            "Director Remuneration",
            "Bank Charges",
            "Investments",
            "Cash Withdrawal",
            "Transfers",
            "Miscellaneous"
        ]

        row_cursor = start_row + 1
        for cat in category_heads:
            dr_cnt_f = f'=COUNTIFS(tblTransactions[Category],"{cat}",tblTransactions[Transaction Type],"DEBIT")'
            dr_sum_f = f'=SUMIFS(tblTransactions[Debit],tblTransactions[Category],"{cat}")'
            cr_cnt_f = f'=COUNTIFS(tblTransactions[Category],"{cat}",tblTransactions[Transaction Type],"CREDIT")'
            cr_sum_f = f'=SUMIFS(tblTransactions[Credit],tblTransactions[Category],"{cat}")'
            net_f = f"=E{row_cursor}-C{row_cursor}"

            ws.append([cat, dr_cnt_f, dr_sum_f, cr_cnt_f, cr_sum_f, net_f])

            ws.cell(row=row_cursor, column=1).font = cls.BOLD_DATA_FONT
            ws.cell(row=row_cursor, column=2).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=3).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=4).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=5).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=6).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=6).font = cls.BOLD_DATA_FONT

            for c in range(1, 7):
                ws.cell(row=row_cursor, column=c).border = cls.THIN_BORDER

            row_cursor += 1

        # Total Row
        tot_row = row_cursor
        ws.cell(row=tot_row, column=1, value="TOTAL").font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=2, value=f"=SUM(B{start_row+1}:B{tot_row-1})").number_format = cls.INTEGER_FORMAT
        ws.cell(row=tot_row, column=2).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=3, value=f"=SUM(C{start_row+1}:C{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=3).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=4, value=f"=SUM(D{start_row+1}:D{tot_row-1})").number_format = cls.INTEGER_FORMAT
        ws.cell(row=tot_row, column=4).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=5, value=f"=SUM(E{start_row+1}:E{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=5).font = cls.BOLD_DATA_FONT
        ws.cell(row=tot_row, column=6, value=f"=SUM(F{start_row+1}:F{tot_row-1})").number_format = cls.CURRENCY_FORMAT
        ws.cell(row=tot_row, column=6).font = cls.BOLD_DATA_FONT

        for c in range(1, 7):
            ws.cell(row=tot_row, column=c).border = cls.TOTAL_ROW_BORDER

        cls._autofit_columns(ws, min_width=16)

    @classmethod
    def _build_top_transactions_sheet(cls, wb: Workbook, transactions: List[Any]):
        ws = wb.create_sheet(title="09_Top_Transactions")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "TOP TRANSACTIONS INTELLIGENCE DOSSIER"
        ws["A1"].font = cls.SECTION_FONT

        # Part 1: Top 15 Largest Outflows
        ws["A3"] = "1. TOP 15 LARGEST DEBITS (OUTFLOWS)"
        ws["A3"].font = cls.BOLD_DATA_FONT

        headers = ["Rank", "Date", "Narration", "Amount (₹)", "Payment Mode", "Category", "Reference"]
        ws.append([])  # Row 4 blank
        ws.cell(row=4, column=1, value="Rank")  # overwritten by append below
        start_dr_row = 4
        for c_idx, h in enumerate(headers):
            cell = ws.cell(row=start_dr_row, column=c_idx + 1, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.NAVY_HEADER_FILL
            cell.border = cls.HEADER_BORDER

        debits = sorted([t for t in transactions if Decimal(str(t.debit_amount or 0)) > 0],
                        key=lambda x: Decimal(str(x.debit_amount)), reverse=True)[:15]

        r_cursor = start_dr_row + 1
        for idx, t in enumerate(debits):
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            ws.cell(row=r_cursor, column=1, value=idx + 1).alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=2, value=t_date).number_format = cls.DATE_FORMAT
            ws.cell(row=r_cursor, column=2).alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=3, value=t.narration)
            ws.cell(row=r_cursor, column=4, value=float(t.debit_amount)).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r_cursor, column=4).font = cls.BOLD_DATA_FONT
            ws.cell(row=r_cursor, column=5, value=t.payment_mode or "TRANSFER").alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=6, value=t.category or "Miscellaneous")
            ws.cell(row=r_cursor, column=7, value=t.reference_number or "")

            for c in range(1, 8):
                ws.cell(row=r_cursor, column=c).border = cls.THIN_BORDER
            r_cursor += 1

        # Part 2: Top 15 Largest Inflows
        r_cursor += 2
        ws.cell(row=r_cursor, column=1, value="2. TOP 15 LARGEST CREDITS (INFLOWS)").font = cls.BOLD_DATA_FONT
        r_cursor += 1

        start_cr_row = r_cursor
        for c_idx, h in enumerate(headers):
            cell = ws.cell(row=start_cr_row, column=c_idx + 1, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.NAVY_HEADER_FILL
            cell.border = cls.HEADER_BORDER

        credits = sorted([t for t in transactions if Decimal(str(t.credit_amount or 0)) > 0],
                         key=lambda x: Decimal(str(x.credit_amount)), reverse=True)[:15]

        r_cursor = start_cr_row + 1
        for idx, t in enumerate(credits):
            t_date = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date() if t.transaction_date else None
            )
            ws.cell(row=r_cursor, column=1, value=idx + 1).alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=2, value=t_date).number_format = cls.DATE_FORMAT
            ws.cell(row=r_cursor, column=2).alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=3, value=t.narration)
            ws.cell(row=r_cursor, column=4, value=float(t.credit_amount)).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=r_cursor, column=4).font = cls.BOLD_DATA_FONT
            ws.cell(row=r_cursor, column=5, value=t.payment_mode or "TRANSFER").alignment = Alignment(horizontal="center")
            ws.cell(row=r_cursor, column=6, value=t.category or "Miscellaneous")
            ws.cell(row=r_cursor, column=7, value=t.reference_number or "")

            for c in range(1, 8):
                ws.cell(row=r_cursor, column=c).border = cls.THIN_BORDER
            r_cursor += 1

        cls._autofit_columns(ws, min_width=14)

    @classmethod
    def _build_daily_analysis_sheet(cls, wb: Workbook, transactions: List[Any]):
        ws = wb.create_sheet(title="10_Daily_Analysis")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "DAILY TRANSACTION ACTIVITY & CASH FLOW"
        ws["A1"].font = cls.SECTION_FONT

        headers = [
            "Date", "Day of Week", "Debit Count", "Total Debit (₹)",
            "Credit Count", "Total Credit (₹)", "Net Cash Flow (₹)"
        ]

        start_row = 3
        ws.append(headers)
        cls._style_header_row(ws, start_row)

        # Collect sorted unique dates
        date_set = set()
        for t in transactions:
            if t.transaction_date:
                dt = t.transaction_date if isinstance(t.transaction_date, (date, datetime)) else (
                    datetime.strptime(str(t.transaction_date), "%Y-%m-%d").date()
                )
                date_set.add(dt)

        sorted_dates = sorted(list(date_set))

        row_cursor = start_row + 1
        for dt in sorted_dates:
            d_expr = f"DATE({dt.year},{dt.month},{dt.day})"
            day_formula = f'=TEXT(A{row_cursor},"dddd")'
            dr_count_f = f'=COUNTIFS(tblTransactions[Transaction Date],A{row_cursor},tblTransactions[Transaction Type],"DEBIT")'
            dr_sum_f = f'=SUMIFS(tblTransactions[Debit],tblTransactions[Transaction Date],A{row_cursor})'
            cr_count_f = f'=COUNTIFS(tblTransactions[Transaction Date],A{row_cursor},tblTransactions[Transaction Type],"CREDIT")'
            cr_sum_f = f'=SUMIFS(tblTransactions[Credit],tblTransactions[Transaction Date],A{row_cursor})'
            net_f = f"=F{row_cursor}-D{row_cursor}"

            ws.append([
                dt,
                day_formula,
                dr_count_f,
                dr_sum_f,
                cr_count_f,
                cr_sum_f,
                net_f
            ])

            ws.cell(row=row_cursor, column=1).number_format = cls.DATE_FORMAT
            ws.cell(row=row_cursor, column=1).alignment = Alignment(horizontal="center")
            ws.cell(row=row_cursor, column=2).alignment = Alignment(horizontal="center")
            ws.cell(row=row_cursor, column=3).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=4).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=5).number_format = cls.INTEGER_FORMAT
            ws.cell(row=row_cursor, column=6).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=7).number_format = cls.CURRENCY_FORMAT
            ws.cell(row=row_cursor, column=7).font = cls.BOLD_DATA_FONT

            for c in range(1, 8):
                ws.cell(row=row_cursor, column=c).border = cls.THIN_BORDER

            row_cursor += 1

        # Total Row
        if sorted_dates:
            tot_row = row_cursor
            ws.cell(row=tot_row, column=1, value="TOTAL").font = cls.BOLD_DATA_FONT
            ws.cell(row=tot_row, column=1).alignment = Alignment(horizontal="center")
            ws.cell(row=tot_row, column=3, value=f"=SUM(C{start_row+1}:C{tot_row-1})").number_format = cls.INTEGER_FORMAT
            ws.cell(row=tot_row, column=3).font = cls.BOLD_DATA_FONT
            ws.cell(row=tot_row, column=4, value=f"=SUM(D{start_row+1}:D{tot_row-1})").number_format = cls.CURRENCY_FORMAT
            ws.cell(row=tot_row, column=4).font = cls.BOLD_DATA_FONT
            ws.cell(row=tot_row, column=5, value=f"=SUM(E{start_row+1}:E{tot_row-1})").number_format = cls.INTEGER_FORMAT
            ws.cell(row=tot_row, column=5).font = cls.BOLD_DATA_FONT
            ws.cell(row=tot_row, column=6, value=f"=SUM(F{start_row+1}:F{tot_row-1})").number_format = cls.CURRENCY_FORMAT
            ws.cell(row=tot_row, column=6).font = cls.BOLD_DATA_FONT
            ws.cell(row=tot_row, column=7, value=f"=SUM(G{start_row+1}:G{tot_row-1})").number_format = cls.CURRENCY_FORMAT
            ws.cell(row=tot_row, column=7).font = cls.BOLD_DATA_FONT

            for c in range(1, 8):
                ws.cell(row=tot_row, column=c).border = cls.TOTAL_ROW_BORDER

        cls._autofit_columns(ws, min_width=14)

    @classmethod
    def _build_reconciliation_sheet(cls, wb: Workbook, statement: Any, reconciliation_report: dict):
        ws = wb.create_sheet(title="12_Reconciliation")
        ws.views.sheetView[0].showGridLines = True

        ws["B2"] = "ICAI BALANCE CONTINUITY & MATHEMATICAL RECONCILIATION"
        ws["B2"].font = cls.TITLE_FONT
        ws["B3"] = "Fundamental Invariant: Opening Balance + Total Credits - Total Debits = Closing Balance"
        ws["B3"].font = cls.MUTED_FONT

        # Reconciliation Table
        ws["B5"] = "ICAI RECONCILIATION COMPONENT"
        ws["B5"].font = cls.HEADER_FONT
        ws["B5"].fill = cls.NAVY_HEADER_FILL
        ws["C5"] = "AMOUNT (₹)"
        ws["C5"].font = cls.HEADER_FONT
        ws["C5"].fill = cls.NAVY_HEADER_FILL
        ws["D5"] = "MATHEMATICAL LOGIC / AUDIT SOURCE"
        ws["D5"].font = cls.HEADER_FONT
        ws["D5"].fill = cls.NAVY_HEADER_FILL

        recon_steps = [
            ("Opening Balance", float(statement.opening_balance or 0.0), cls.CURRENCY_FORMAT, "Stated Opening Balance from Bank Statement Header"),
            ("(+) Total Credits (Audited Inflows)", "=SUM(tblTransactions[Credit])", cls.CURRENCY_FORMAT, "Sum of all extracted credit transactions"),
            ("(-) Total Debits (Audited Outflows)", "=SUM(tblTransactions[Debit])", cls.CURRENCY_FORMAT, "Sum of all extracted debit transactions"),
            ("(=) Calculated Closing Balance", "=C6+C7-C8", cls.CURRENCY_FORMAT, "Formula: Opening + Credits - Debits"),
            ("Stated Closing Balance", float(statement.closing_balance or 0.0), cls.CURRENCY_FORMAT, "Stated Closing Balance reported by Bank Statement"),
            ("Variance / Discrepancy", "=C9-C10", cls.CURRENCY_FORMAT, "Formula: Calculated Closing - Stated Closing"),
            ("Audit Reconciliation Result", '=IF(ABS(C11)<=\'13_Reference_Data\'!B5,"RECONCILED","DISCREPANCY DETECTED")', "@", "Verified against tolerance threshold in 13_Reference_Data!B5")
        ]

        for idx, (label, val, fmt, note) in enumerate(recon_steps):
            r = 6 + idx
            ws.cell(row=r, column=2, value=label).font = cls.BOLD_DATA_FONT if "Balance" in label or "Result" in label else cls.DATA_FONT
            val_cell = ws.cell(row=r, column=3, value=val)
            val_cell.font = cls.BOLD_DATA_FONT
            val_cell.number_format = fmt
            ws.cell(row=r, column=4, value=note).font = cls.MUTED_FONT

            if label == "Audit Reconciliation Result":
                val_cell.fill = cls.SUCCESS_FILL
                val_cell.font = cls.SUCCESS_FONT

            for c in range(2, 5):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Step-by-Step Running Continuity Verification
        ws["B15"] = "TRANSACTION RUNNING BALANCE CONTINUITY AUDIT"
        ws["B15"].font = cls.SECTION_FONT

        broken = reconciliation_report.get("broken_steps", [])
        if not broken:
            ws.cell(row=17, column=2, value="✓ ZERO BROKEN STEPS DETECTED").font = cls.SUCCESS_FONT
            ws.cell(row=17, column=2).fill = cls.SUCCESS_FILL
            ws.cell(row=18, column=2, value="Every individual transaction running balance strictly equals previous balance - debit + credit.").font = cls.MUTED_FONT
        else:
            ws.cell(row=17, column=2, value=f"⚠ {len(broken)} BALANCE LEAPS DETECTED IN TRANSACTION SEQUENCE").font = cls.ALERT_FONT
            ws.cell(row=17, column=2).fill = cls.ALERT_FILL

            b_headers = ["Break #", "Row No", "Expected Balance (₹)", "Reported Balance (₹)", "Discrepancy (₹)"]
            for c_i, bh in enumerate(b_headers):
                cell = ws.cell(row=19, column=c_i + 2, value=bh)
                cell.font = cls.HEADER_FONT
                cell.fill = cls.ALERT_FILL
                cell.font = cls.ALERT_FONT
                cell.border = cls.THIN_BORDER

            for b_idx, b in enumerate(broken):
                br_row = 20 + b_idx
                ws.cell(row=br_row, column=2, value=b_idx + 1).alignment = Alignment(horizontal="center")
                ws.cell(row=br_row, column=3, value=b.get("row_index", "")).alignment = Alignment(horizontal="center")
                ws.cell(row=br_row, column=4, value=float(b.get("expected_balance", 0))).number_format = cls.CURRENCY_FORMAT
                ws.cell(row=br_row, column=5, value=float(b.get("reported_balance", 0))).number_format = cls.CURRENCY_FORMAT
                ws.cell(row=br_row, column=6, value=float(b.get("difference", 0))).number_format = cls.CURRENCY_FORMAT
                ws.cell(row=br_row, column=6).font = cls.ALERT_FONT

                for c in range(2, 7):
                    ws.cell(row=br_row, column=c).border = cls.THIN_BORDER

        cls._autofit_columns(ws, min_width=25)

    @classmethod
    def _build_review_required_sheet(cls, wb: Workbook, review_items: list):
        ws = wb.create_sheet(title="12_Review_Required")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "AUDITOR EXCEPTION & VERIFICATION QUEUE"
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = "Flags low confidence scores, unusual round-sum movements, continuity anomalies & unclassified items"
        ws["A2"].font = cls.MUTED_FONT

        headers = [
            "Item #", "Transaction Date", "Narration", "Debit (₹)", "Credit (₹)",
            "Issue Category", "Detailed Audit Finding", "Audit Status", "Auditor Initials / Notes"
        ]

        start_row = 4
        ws.append(headers)
        cls._style_header_row(ws, start_row)

        if not review_items:
            # Clean zero-exception state
            ws.cell(row=5, column=1, value="No review items flagged").alignment = Alignment(horizontal="center")
            ws.cell(row=5, column=7, value="All transactions passed automated integrity, continuity & confidence thresholds.").font = cls.SUCCESS_FONT
            for c in range(1, len(headers) + 1):
                ws.cell(row=5, column=c).border = cls.THIN_BORDER
        else:
            row_cursor = start_row + 1
            for idx, r_item in enumerate(review_items):
                txn = getattr(r_item, 'transaction', None)
                t_date = getattr(txn, 'transaction_date', None) if txn else None
                narr = getattr(txn, 'narration', 'Transaction flagged during automated audit') if txn else "Flagged Transaction"
                dr = float(getattr(txn, 'debit_amount', 0.0)) if txn else 0.0
                cr = float(getattr(txn, 'credit_amount', 0.0)) if txn else 0.0
                issue_code = getattr(r_item, 'issue_code', 'POTENTIAL_ANOMALY')
                desc = getattr(r_item, 'issue_description', 'Requires review')
                status_val = getattr(r_item, 'status', 'PENDING')

                ws.append([
                    idx + 1,
                    t_date,
                    narr,
                    dr,
                    cr,
                    issue_code,
                    desc,
                    status_val,
                    ""
                ])

                ws.cell(row=row_cursor, column=1).alignment = Alignment(horizontal="center")
                ws.cell(row=row_cursor, column=2).number_format = cls.DATE_FORMAT
                ws.cell(row=row_cursor, column=2).alignment = Alignment(horizontal="center")
                ws.cell(row=row_cursor, column=4).number_format = cls.CURRENCY_FORMAT
                ws.cell(row=row_cursor, column=5).number_format = cls.CURRENCY_FORMAT
                ws.cell(row=row_cursor, column=6).font = cls.BOLD_DATA_FONT
                ws.cell(row=row_cursor, column=8).alignment = Alignment(horizontal="center")
                ws.cell(row=row_cursor, column=8).font = cls.ALERT_FONT if status_val == "PENDING" else cls.SUCCESS_FONT

                for c in range(1, len(headers) + 1):
                    ws.cell(row=row_cursor, column=c).border = cls.THIN_BORDER

                row_cursor += 1

        cls._autofit_columns(ws, min_width=15)

    @classmethod
    def _build_reference_data_sheet(cls, wb: Workbook, custom_threshold: float = 50000.0):
        ws = wb.create_sheet(title="13_Reference_Data")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "AUDIT CONTROL PARAMETERS & REFERENCE MASTERS"
        ws["A1"].font = cls.SECTION_FONT
        ws["A2"] = "Configuration thresholds and master tables utilized by workbook dynamic formulas"
        ws["A2"].font = cls.MUTED_FONT

        # Thresholds Master
        ws["A4"] = "Parameter Name"
        ws["A4"].font = cls.HEADER_FONT
        ws["A4"].fill = cls.NAVY_HEADER_FILL
        ws["B4"] = "Configured Value"
        ws["B4"].font = cls.HEADER_FONT
        ws["B4"].fill = cls.NAVY_HEADER_FILL
        ws["C4"] = "Unit / Description"
        ws["C4"].font = cls.HEADER_FONT
        ws["C4"].fill = cls.NAVY_HEADER_FILL

        thresholds = [
            ("High Value Transaction Threshold", 50000.00, "INR (Transactions above this require tax scrutiny)"),
            ("Balance Invariant Tolerance", 1.00, "INR (Rounding variance allowance for reconciliation)"),
            ("Cash Monitoring Threshold", 200000.00, "INR (Section 269ST threshold for cash transactions)"),
            ("Confidence Quality Benchmark", 0.90, "90% minimum threshold for automatic validation"),
        ]

        for idx, (p_name, p_val, p_desc) in enumerate(thresholds):
            r = 5 + idx
            ws.cell(row=r, column=1, value=p_name).font = cls.BOLD_DATA_FONT
            v_cell = ws.cell(row=r, column=2, value=p_val)
            v_cell.font = cls.BOLD_DATA_FONT
            if "Threshold" in p_name or "Tolerance" in p_name:
                v_cell.number_format = cls.CURRENCY_FORMAT
            elif "Benchmark" in p_name:
                v_cell.number_format = cls.PERCENT_FORMAT

            ws.cell(row=r, column=3, value=p_desc).font = cls.MUTED_FONT

            for c in range(1, 4):
                ws.cell(row=r, column=c).border = cls.THIN_BORDER

        # Master Modes List
        ws["E4"] = "Master Payment Modes"
        ws["E4"].font = cls.HEADER_FONT
        ws["E4"].fill = cls.NAVY_HEADER_FILL

        master_modes = ["UPI", "NEFT", "RTGS", "IMPS", "CHEQUE", "CASH", "CARD", "NETBANKING", "CHARGES", "TRANSFER", "OTHERS"]
        for idx, m in enumerate(master_modes):
            r = 5 + idx
            ws.cell(row=r, column=5, value=m).font = cls.DATA_FONT
            ws.cell(row=r, column=5).border = cls.THIN_BORDER

        # Master Categories List
        ws["G4"] = "Master Accounting Categories"
        ws["G4"].font = cls.HEADER_FONT
        ws["G4"].fill = cls.NAVY_HEADER_FILL

        master_cats = [
            "Salary", "Rent", "Tax", "Vendor Payment", "Utilities",
            "Professional Fees", "Director Remuneration", "Bank Charges",
            "Investments", "Cash Withdrawal", "Transfers", "Miscellaneous"
        ]
        for idx, cat in enumerate(master_cats):
            r = 5 + idx
            ws.cell(row=r, column=7, value=cat).font = cls.DATA_FONT
            ws.cell(row=r, column=7).border = cls.THIN_BORDER

        cls._autofit_columns(ws, min_width=20)

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _get_financial_year(statement_date) -> str:
        if not statement_date:
            curr_yr = datetime.now().year
            return f"FY {curr_yr}-{str(curr_yr+1)[-2:]}"
        try:
            if isinstance(statement_date, (date, datetime)):
                dt = statement_date
            else:
                dt = datetime.strptime(str(statement_date), "%Y-%m-%d").date()
            if dt.month >= 4:
                return f"FY {dt.year}-{str(dt.year+1)[-2:]}"
            else:
                return f"FY {dt.year-1}-{str(dt.year)[-2:]}"
        except Exception:
            return "FY 2025-26"
