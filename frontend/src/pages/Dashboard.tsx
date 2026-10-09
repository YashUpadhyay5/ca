import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  ArrowRightLeft,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ShieldAlert,
  Building,
  Upload,
  Loader2,
} from 'lucide-react';
import { Statement, Client } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface DashboardProps {
  statements: Statement[];
  clients: Client[];
  reviewCount: number;
  onSelectStatement: (stmtId: string) => void;
  onOpenUpload: () => void;
  onNavigateTab: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  statements,
  clients,
  reviewCount,
  onSelectStatement,
  onOpenUpload,
  onNavigateTab,
}) => {
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [exportingCsvId, setExportingCsvId] = useState<string | null>(null);

  const totalTxns = statements.reduce((acc, s) => acc + s.total_transactions, 0);
  const totalCredits = statements.reduce((acc, s) => acc + Number(s.total_credits), 0);
  const totalDebits = statements.reduce((acc, s) => acc + Number(s.total_debits), 0);
  const netCashflow = totalCredits - totalDebits;

  const reconciledCount = statements.filter((s) => s.reconciliation_status === 'RECONCILED').length;
  const discrepancyCount = statements.filter((s) => s.reconciliation_status === 'DISCREPANCY_DETECTED').length;

  const handleExportExcel = async (statementId: string) => {
    try {
      setExportingId(statementId);
      const response = await apiClient.post(
        '/exports/excel',
        { statement_id: statementId },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BankStatement_Analysis_${statementId.slice(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExportingId(null);
    }
  };

  const handleExportCSV = async (statementId: string) => {
    try {
      setExportingCsvId(statementId);
      const response = await apiClient.post(
        '/exports/csv',
        { statement_id: statementId },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BankStatement_Transactions_${statementId.slice(0, 8)}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('CSV export failed:', err);
    } finally {
      setExportingCsvId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-900/40 via-slate-900 to-indigo-900/30 border border-blue-800/30 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">CA Practice Intelligence Dashboard</h2>
          <p className="text-xs text-slate-400 mt-1">
            ICAI Compliant Audit Trail • Step-by-Step Balance Continuity • Multi-Bank PDF Extraction Engine
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {statements.length > 0 && (
            <button
              onClick={() => handleExportExcel(statements[0].id)}
              disabled={exportingId === statements[0].id}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition flex items-center gap-1.5"
            >
              {exportingId === statements[0].id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="w-4 h-4" />
              )}
              <span>Export to Excel (.xlsx)</span>
            </button>
          )}
          <button
            onClick={onOpenUpload}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition flex items-center gap-1.5"
          >
            <span>+ Upload Statement PDF</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Credits */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Credits</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-3">
            {formatCurrency(totalCredits)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Across uploaded client statements</div>
        </div>

        {/* Card 2: Total Debits */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Debits</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <TrendingDown className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-400 font-mono mt-3">
            {formatCurrency(totalDebits)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Total outflow audited</div>
        </div>

        {/* Card 3: Net Cash Flow */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Net Movement</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <ArrowRightLeft className="w-4 h-4" />
            </div>
          </div>
          <div className={`text-2xl font-bold font-mono mt-3 ${netCashflow >= 0 ? 'text-blue-400' : 'text-amber-400'}`}>
            {formatCurrency(netCashflow)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">{totalTxns.toLocaleString()} Transactions Extracted</div>
        </div>

        {/* Card 4: Audit Status */}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Review Queue</span>
            <div className={`p-2 rounded-lg ${reviewCount > 0 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white font-mono mt-3">
            {reviewCount} <span className="text-xs font-sans text-slate-400 font-normal">items</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5">
            {reviewCount === 0 ? (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> All items verified
              </span>
            ) : (
              <span className="text-amber-400">CA verification pending</span>
            )}
          </div>
        </div>
      </div>

      {/* Reconciliation Health bar */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Reconciliation Invariant Status</div>
            <div className="text-xs text-slate-400">
              {reconciledCount} Statements Reconciled (Opening + Credits - Debits == Closing) • {discrepancyCount} Discrepant
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onNavigateTab('reconciliation')}
            className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            Launch Reconciliation Studio
          </button>
        </div>
      </div>

      {/* Recent Bank Statements Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-bold text-white">Processed Bank Statements</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">{statements.length} Total</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-6 py-3">Bank Name</th>
                <th className="px-6 py-3">Account No</th>
                <th className="px-6 py-3">Period</th>
                <th className="px-6 py-3 text-right">Transactions</th>
                <th className="px-6 py-3 text-right">Closing Balance</th>
                <th className="px-6 py-3 text-center">Status</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {statements.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    <div className="max-w-md mx-auto space-y-3">
                      <div className="w-12 h-12 bg-blue-600/10 text-blue-400 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto">
                        <Upload className="w-6 h-6" />
                      </div>
                      <div className="text-sm font-bold text-white">No Bank Statements Uploaded Yet</div>
                      <p className="text-xs text-slate-400">
                        Upload any Bank Statement PDF (HDFC, SBI, ICICI, Axis, Kotak, etc.) to automatically extract transactions, audit balance continuity, and generate complete 13-sheet CA financial analysis with Excel export.
                      </p>
                      <button
                        onClick={onOpenUpload}
                        className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 transition inline-flex items-center gap-1.5"
                      >
                        <Upload className="w-4 h-4" />
                        <span>Upload Bank Statement PDF</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ) : (
                statements.map((stmt) => (
                  <tr key={stmt.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-3.5 font-medium text-white flex items-center gap-2">
                      <Building className="w-4 h-4 text-slate-400" />
                      {stmt.bank_name}
                    </td>
                    <td className="px-6 py-3.5 font-mono text-slate-400">
                      {stmt.account_number_detected || 'Masked'}
                    </td>
                    <td className="px-6 py-3.5 text-slate-400">
                      {formatDate(stmt.period_start)} - {formatDate(stmt.period_end)}
                    </td>
                    <td className="px-6 py-3.5 text-right font-mono text-slate-300">
                      {stmt.total_transactions}
                    </td>
                    <td className="px-6 py-3.5 text-right font-mono text-emerald-400 font-medium">
                      {formatCurrency(stmt.closing_balance)}
                    </td>
                    <td className="px-6 py-3.5 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          stmt.reconciliation_status === 'RECONCILED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {stmt.reconciliation_status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleExportExcel(stmt.id)}
                          disabled={exportingId === stmt.id}
                          className="px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 text-xs font-medium border border-emerald-500/30 transition flex items-center gap-1"
                          title="Download Formatted Excel Workbook"
                        >
                          {exportingId === stmt.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <FileSpreadsheet className="w-3.5 h-3.5" />
                          )}
                          <span>Excel</span>
                        </button>
                        <button
                          onClick={() => handleExportCSV(stmt.id)}
                          disabled={exportingCsvId === stmt.id}
                          className="px-2.5 py-1 rounded bg-slate-700/50 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-600/40 transition flex items-center gap-1"
                          title="Download Tabular CSV"
                        >
                          {exportingCsvId === stmt.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <ArrowRightLeft className="w-3.5 h-3.5" />
                          )}
                          <span>CSV</span>
                        </button>
                        <button
                          onClick={() => onSelectStatement(stmt.id)}
                          className="px-2.5 py-1 rounded bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 text-xs font-medium border border-blue-500/30 transition flex items-center gap-1"
                        >
                          <span>Analyze</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
