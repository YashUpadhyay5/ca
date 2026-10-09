export interface User {
  id: string;
  org_id: string;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'CA' | 'AUDITOR';
  is_active: boolean;
}

export interface BankAccount {
  id: string;
  client_id: string;
  bank_name: string;
  account_number_masked: string;
  ifsc?: string;
  account_type: string;
  branch?: string;
}

export interface Client {
  id: string;
  org_id: string;
  name: string;
  pan?: string;
  gstin?: string;
  email?: string;
  phone?: string;
  notes?: string;
  created_at: string;
  bank_accounts: BankAccount[];
}

export interface Document {
  id: string;
  org_id: string;
  client_id: string;
  file_name: string;
  file_size: number;
  file_hash: string;
  page_count: number;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  is_scanned: boolean;
  error_message?: string;
  uploaded_at: string;
}

export interface Statement {
  id: string;
  document_id: string;
  bank_account_id?: string;
  bank_name: string;
  account_number_detected?: string;
  period_start?: string;
  period_end?: string;
  opening_balance: number;
  closing_balance: number;
  calculated_closing_balance: number;
  balance_discrepancy: number;
  reconciliation_status: 'RECONCILED' | 'DISCREPANCY_DETECTED' | 'UNVERIFIED';
  total_transactions: number;
  total_credits: number;
  total_debits: number;
  net_movement: number;
  parser_used: string;
  confidence_avg: number;
  created_at: string;
}

export interface Transaction {
  id: string;
  statement_id: string;
  transaction_date: string;
  value_date?: string;
  narration: string;
  raw_text: string;
  reference_number?: string;
  cheque_number?: string;
  debit_amount: number;
  credit_amount: number;
  balance: number;
  payment_mode: string;
  category: string;
  subcategory?: string;
  counterparty?: string;
  upi_id?: string;
  source_page: number;
  source_row: number;
  confidence_score: number;
  validation_status: 'VALIDATED' | 'REVIEW_REQUIRED' | 'MANUAL_CORRECTED';
  is_internal_transfer: boolean;
  is_potential_duplicate: boolean;
  is_anomaly: boolean;
  notes?: string;
}

export interface PaginatedTransactions {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  total_debits: number;
  total_credits: number;
  net_amount: number;
}

export interface MonthlyTrend {
  month_name: string;
  year: number;
  fiscal_month_index: number;
  credits: number;
  debits: number;
  net_movement: number;
  transaction_count: number;
  average_transaction: number;
}

export interface PaymentModeItem {
  mode: string;
  count: number;
  total_amount: number;
  percentage: number;
}

export interface CategoryItem {
  category: string;
  debit_amount: number;
  credit_amount: number;
  transaction_count: number;
  percentage_of_debit: number;
}

export interface TopTransaction {
  id: string;
  date: string;
  narration: string;
  amount: number;
  transaction_type: string;
  payment_mode: string;
  counterparty?: string;
  category: string;
}

export interface TaxItem {
  tax_type: string;
  total_paid: number;
  transaction_count: number;
  transactions: TopTransaction[];
}

export interface FinancialOverview {
  statement_id: string;
  bank_name: string;
  period_start?: string;
  period_end?: string;
  opening_balance: number;
  closing_balance: number;
  calculated_closing_balance: number;
  balance_discrepancy: number;
  reconciliation_status: string;
  total_credits: number;
  total_debits: number;
  net_movement: number;
  total_transactions: number;
  debit_count: number;
  credit_count: number;
  largest_credit: number;
  largest_debit: number;
  average_transaction: number;
  median_transaction: number;
  std_dev_transaction: number;
  highest_debit_day?: string;
  highest_credit_day?: string;
  anomaly_count: number;
  potential_duplicate_count: number;
  review_required_count: number;
  monthly_trends: MonthlyTrend[];
  payment_modes: PaymentModeItem[];
  top_categories: CategoryItem[];
  top_debits: TopTransaction[];
  top_credits: TopTransaction[];
  tax_summary: TaxItem[];
}

export interface BalanceStepItem {
  row_index: number;
  date: string;
  narration: string;
  debit: number;
  credit: number;
  previous_balance: number;
  expected_balance: number;
  reported_balance: number;
  difference: number;
  is_continuity_broken: boolean;
}

export interface ReconciliationReport {
  statement_id: string;
  bank_name: string;
  opening_balance: number;
  closing_balance: number;
  sum_credits: number;
  sum_debits: number;
  expected_closing_balance: number;
  discrepancy: number;
  status: string;
  broken_step_count: number;
  broken_steps: BalanceStepItem[];
}

export interface ReviewItem {
  id: string;
  transaction_id: string;
  statement_id: string;
  date: string;
  narration: string;
  raw_text: string;
  debit_amount: number;
  credit_amount: number;
  balance: number;
  issue_code: string;
  issue_description: string;
  confidence_score: number;
  status: string;
  category: string;
  payment_mode: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  entity_name: string;
  entity_id: string;
  old_value?: any;
  new_value?: any;
  details?: string;
  user_email: string;
  timestamp: string;
}
