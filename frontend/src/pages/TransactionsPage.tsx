import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  Download,
  ArrowUpDown,
  FileSpreadsheet,
  FileText,
  Edit2,
  Check,
  X,
  Eye,
  Tag,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Transaction, Statement, PaginatedTransactions } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface TransactionsPageProps {
  statements: Statement[];
  selectedStatementId: string | null;
  onSelectStatementId: (id: string) => void;
}

export const TransactionsPage: React.FC<TransactionsPageProps> = ({
  statements,
  selectedStatementId,
  onSelectStatementId,
}) => {
  const [activeStatementId, setActiveStatementId] = useState<string>(
    selectedStatementId || statements[0]?.id || ''
  );
  const [data, setData] = useState<PaginatedTransactions | null>(null);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [txnType, setTxnType] = useState<string>('ALL'); // ALL, DEBIT, CREDIT
  const [paymentMode, setPaymentMode] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('transaction_date');
  const [sortDir, setSortDir] = useState<string>('asc');
  const [page, setPage] = useState<number>(1);

  // Selection & modals
  const [selectedTxnIds, setSelectedTxnIds] = useState<string[]>([]);
  const [inspectTxn, setInspectTxn] = useState<Transaction | null>(null);
  const [editTxn, setEditTxn] = useState<Transaction | null>(null);
  const [editCategory, setEditCategory] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [editReason, setEditReason] = useState('');

  // Bulk categorize modal
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkCategory, setBulkCategory] = useState('Business Expense');

  const categoriesList = [
    'Tax',
    'Salary',
    'Rent',
    'Utilities',
    'EMI',
    'Investment',
    'Food',
    'Travel',
    'Fuel',
    'Shopping',
    'Bank Charges',
    'Cash',
    'Transfer',
    'Business Expense',
    'Miscellaneous',
  ];

  const paymentModesList = ['UPI', 'NEFT', 'RTGS', 'IMPS', 'ATM', 'POS', 'CHEQUE', 'CASH', 'TRANSFER'];

  const fetchTransactions = async () => {
    if (!activeStatementId) return;
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: 50,
        sort_by: sortBy,
        sort_dir: sortDir,
      };
      if (search) params.search = search;
      if (txnType !== 'ALL') params.transaction_type = txnType;
      if (paymentMode) params.payment_mode = paymentMode;
      if (category) params.category = category;

      const res = await apiClient.get(`/statements/${activeStatementId}/transactions`, { params });
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStatementId && selectedStatementId !== activeStatementId) {
      setActiveStatementId(selectedStatementId);
    }
  }, [selectedStatementId]);

  useEffect(() => {
    fetchTransactions();
  }, [activeStatementId, search, txnType, paymentMode, category, sortBy, sortDir, page]);

  const handleToggleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('asc');
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked && data) {
      setSelectedTxnIds(data.items.map((i) => i.id));
    } else {
      setSelectedTxnIds([]);
    }
  };

  const handleToggleSelectRow = (id: string) => {
    setSelectedTxnIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSaveInlineEdit = async () => {
    if (!editTxn) return;
    try {
      await apiClient.patch(`/transactions/${editTxn.id}`, {
        category: editCategory,
        notes: editNotes,
        reason: editReason || 'Manual audit modification by CA',
      });
      setEditTxn(null);
      fetchTransactions();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveBulkCategorize = async () => {
    if (selectedTxnIds.length === 0) return;
    try {
      await apiClient.post('/transactions/bulk-categorize', {
        transaction_ids: selectedTxnIds,
        category: bulkCategory,
        reason: 'Bulk categorization by auditor',
      });
      setShowBulkModal(false);
      setSelectedTxnIds([]);
      fetchTransactions();
    } catch (err) {
      console.error(err);
    }
  };

  const handleExportExcel = async () => {
    if (!activeStatementId) return;
    try {
      const res = await apiClient.post(
        '/exports/excel',
        {
          statement_id: activeStatementId,
          transaction_type: txnType,
          payment_mode: paymentMode || undefined,
          category: category || undefined,
        },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Filtered_Audit_Export_${activeStatementId.slice(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    }
  };

  const handleExportCSV = async () => {
    if (!activeStatementId) return;
    try {
      const res = await apiClient.post(
        '/exports/csv',
        {
          statement_id: activeStatementId,
          transaction_type: txnType,
          payment_mode: paymentMode || undefined,
          category: category || undefined,
        },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Transactions_${activeStatementId.slice(0, 8)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      {/* Statement Selector & Quick Actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <label className="text-xs font-semibold text-slate-400 whitespace-nowrap">
            Active Statement:
          </label>
          <select
            value={activeStatementId}
            onChange={(e) => {
              setActiveStatementId(e.target.value);
              onSelectStatementId(e.target.value);
              setPage(1);
            }}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 w-full md:w-64"
          >
            {statements.map((s) => (
              <option key={s.id} value={s.id}>
                {s.bank_name} ({s.account_number_detected || 'Masked'}) • {s.total_transactions} txns
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          {selectedTxnIds.length > 0 && (
            <button
              onClick={() => setShowBulkModal(true)}
              className="px-3 py-1.5 rounded-lg bg-blue-600/30 hover:bg-blue-600/50 border border-blue-500/40 text-blue-200 text-xs font-semibold transition flex items-center gap-1.5"
            >
              <Tag className="w-3.5 h-3.5" />
              <span>Categorize ({selectedTxnIds.length})</span>
            </button>
          )}

          <button
            onClick={handleExportExcel}
            className="px-3.5 py-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-emerald-200 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export Excel (13-Sheet Analysis)</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium transition flex items-center gap-1.5"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search narration, UPI, ref..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Direction Toggle */}
        <div className="flex rounded-lg bg-slate-800 p-0.5 border border-slate-700">
          {(['ALL', 'DEBIT', 'CREDIT'] as const).map((type) => (
            <button
              key={type}
              onClick={() => {
                setTxnType(type);
                setPage(1);
              }}
              className={`flex-1 py-1 text-xs font-medium rounded-md transition ${
                txnType === type ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              {type === 'ALL' ? 'All' : type === 'DEBIT' ? 'Debits' : 'Credits'}
            </button>
          ))}
        </div>

        {/* Payment Mode */}
        <select
          value={paymentMode}
          onChange={(e) => {
            setPaymentMode(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Payment Modes</option>
          {paymentModesList.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        {/* Category */}
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Categories</option>
          {categoriesList.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        {/* Filter Summary Stats */}
        {data && (
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono px-2">
            <span>Dr: <b className="text-rose-400">{formatCurrency(data.total_debits)}</b></span>
            <span>Cr: <b className="text-emerald-400">{formatCurrency(data.total_credits)}</b></span>
          </div>
        )}
      </div>

      {/* Spreadsheet Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto max-h-[580px]">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800 text-slate-300 font-semibold uppercase tracking-wider sticky top-0 z-10 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 w-8">
                  <input
                    type="checkbox"
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    checked={data ? selectedTxnIds.length === data.items.length && data.items.length > 0 : false}
                    className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-0"
                  />
                </th>
                <th
                  onClick={() => handleToggleSort('transaction_date')}
                  className="px-4 py-3 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    <span>Date</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="px-4 py-3 min-w-[240px]">Narration & Counterparty</th>
                <th className="px-4 py-3">Ref / Chq</th>
                <th
                  onClick={() => handleToggleSort('debit_amount')}
                  className="px-4 py-3 text-right cursor-pointer hover:text-white"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Debit Outflow</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th
                  onClick={() => handleToggleSort('credit_amount')}
                  className="px-4 py-3 text-right cursor-pointer hover:text-white"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Credit Inflow</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th
                  onClick={() => handleToggleSort('balance')}
                  className="px-4 py-3 text-right cursor-pointer hover:text-white"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Balance</span>
                    <ArrowUpDown className="w-3 h-3 text-slate-500" />
                  </div>
                </th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 text-center">Audit Lineage</th>
                <th className="px-4 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-slate-400 font-sans">
                    Loading verified transactions...
                  </td>
                </tr>
              ) : !data || data.items.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-slate-500 font-sans">
                    No transactions match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                data.items.map((t) => {
                  const isDebit = t.debit_amount > 0;
                  const isSelected = selectedTxnIds.includes(t.id);
                  return (
                    <tr
                      key={t.id}
                      className={`hover:bg-slate-800/50 transition ${isSelected ? 'bg-blue-600/10' : ''}`}
                    >
                      <td className="px-4 py-2.5">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelectRow(t.id)}
                          className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                        />
                      </td>
                      <td className="px-4 py-2.5 text-slate-400 whitespace-nowrap">
                        {formatDate(t.transaction_date)}
                      </td>
                      <td className="px-4 py-2.5 font-sans">
                        <div className="font-medium text-slate-100 max-w-sm truncate" title={t.narration}>
                          {t.narration}
                        </div>
                        {t.counterparty && (
                          <div className="text-[11px] text-blue-400 flex items-center gap-1 mt-0.5">
                            <span>Party: {t.counterparty}</span>
                            {t.upi_id && <span className="text-slate-500 font-mono">({t.upi_id})</span>}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-slate-500 text-[11px]">
                        {t.reference_number || t.cheque_number || '-'}
                      </td>
                      <td className="px-4 py-2.5 text-right font-medium text-rose-400">
                        {t.debit_amount > 0 ? formatCurrency(t.debit_amount) : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-right font-medium text-emerald-400">
                        {t.credit_amount > 0 ? formatCurrency(t.credit_amount) : '-'}
                      </td>
                      <td className="px-4 py-2.5 text-right text-slate-200">
                        {formatCurrency(t.balance)}
                      </td>
                      <td className="px-4 py-2.5 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                          {t.payment_mode}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-sans">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                          {t.category}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-center font-sans">
                        <button
                          onClick={() => setInspectTxn(t)}
                          title="View PDF Lineage & Raw Source Text"
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] border border-slate-700 transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3 text-blue-400" />
                          <span>p.{t.source_page}</span>
                        </button>
                      </td>
                      <td className="px-4 py-2.5 text-center font-sans">
                        <button
                          onClick={() => {
                            setEditTxn(t);
                            setEditCategory(t.category);
                            setEditNotes(t.notes || '');
                            setEditReason('');
                          }}
                          title="Inline Edit & Re-categorize"
                          className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {data && (
          <div className="px-4 py-3 bg-slate-800/80 border-t border-slate-700 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-3">
            <div>
              Showing {data.items.length > 0 ? (data.page - 1) * data.page_size + 1 : 0} to{' '}
              {Math.min(data.page * data.page_size, data.total)} of {data.total} records
            </div>

            <div className="flex items-center space-x-2">
              <button
                disabled={data.page <= 1}
                onClick={() => setPage(data.page - 1)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-mono text-white px-2">
                Page {data.page} of {data.total_pages}
              </span>
              <button
                disabled={data.page >= data.total_pages}
                onClick={() => setPage(data.page + 1)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Audit Lineage Inspector Modal (Section 2) */}
      {inspectTxn && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                Audit Lineage Proof
              </h3>
              <button onClick={() => setInspectTxn(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60 space-y-2">
                <div className="text-slate-400 font-semibold uppercase text-[10px]">
                  Where did this number come from in the original PDF?
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <span className="text-slate-500 block">PDF Page:</span>
                    <span className="font-mono text-white font-bold">{inspectTxn.source_page}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Row Index:</span>
                    <span className="font-mono text-white font-bold">{inspectTxn.source_row}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Confidence:</span>
                    <span className="font-mono text-emerald-400 font-bold">
                      {(inspectTxn.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">
                  Untouched Original Source Line (Raw OCR / PDF Text):
                </span>
                <pre className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-300 font-mono text-[11px] whitespace-pre-wrap">
                  {inspectTxn.raw_text}
                </pre>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-500 block">Amount Extracted:</span>
                  <span className="font-mono text-white font-semibold">
                    {formatCurrency(inspectTxn.debit_amount > 0 ? inspectTxn.debit_amount : inspectTxn.credit_amount)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block">Reported Balance:</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {formatCurrency(inspectTxn.balance)}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setInspectTxn(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs rounded-lg transition"
              >
                Close Lineage
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inline Edit & Categorize Modal */}
      {editTxn && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-400" />
                Audit Correction & Note
              </h3>
              <button onClick={() => setEditTxn(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Narration:</label>
                <div className="p-2.5 rounded bg-slate-800/80 text-slate-200">{editTxn.narration}</div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Accounting Category:</label>
                <select
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  {categoriesList.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Audit Notes / Reason *:</label>
                <input
                  type="text"
                  required
                  value={editReason}
                  onChange={(e) => setEditReason(e.target.value)}
                  placeholder="e.g. Verified with GST Challan / Tax Invoice"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setEditTxn(null)}
                className="px-4 py-2 text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveInlineEdit}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg shadow-md transition"
              >
                Save & Record Audit Trail
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Categorize Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm shadow-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Bulk Re-categorization</h3>
            <p className="text-xs text-slate-400">
              Apply new category to <b>{selectedTxnIds.length}</b> selected transactions simultaneously.
            </p>
            <div>
              <label className="block text-slate-400 font-semibold mb-1 text-xs">Target Category:</label>
              <select
                value={bulkCategory}
                onChange={(e) => setBulkCategory(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
              >
                {categoriesList.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setShowBulkModal(false)}
                className="px-4 py-2 text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveBulkCategorize}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg transition"
              >
                Apply Category
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
