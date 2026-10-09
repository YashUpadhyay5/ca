import React from 'react';
import {
  FileSpreadsheet,
  Building,
  ArrowUpRight,
  Download,
  Calendar,
  Layers,
  Scale,
  BarChart2,
  Table,
} from 'lucide-react';
import { Statement } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface StatementsPageProps {
  statements: Statement[];
  onSelectStatement: (stmtId: string, tab?: string) => void;
  onOpenUpload: () => void;
}

export const StatementsPage: React.FC<StatementsPageProps> = ({
  statements,
  onSelectStatement,
  onOpenUpload,
}) => {
  const handleExportExcel = async (statementId: string) => {
    try {
      const response = await apiClient.post(
        '/exports/excel',
        { statement_id: statementId },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BankStatement_Audit_${statementId.slice(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Bank Statements</h2>
          <p className="text-xs text-slate-400 mt-1">
            Audited financial datasets extracted from Indian bank statement PDFs
          </p>
        </div>
        <button
          onClick={onOpenUpload}
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center gap-1.5 transition"
        >
          <span>+ Upload PDF</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {statements.map((s) => (
          <div
            key={s.id}
            className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm flex flex-col justify-between space-y-4 hover:border-slate-700 transition"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Building className="w-4 h-4 text-blue-400" />
                    {s.bank_name}
                  </h3>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">
                    Account: {s.account_number_detected || 'Masked'}
                  </div>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    s.reconciliation_status === 'RECONCILED'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  {s.reconciliation_status}
                </span>
              </div>

              {/* Period badge */}
              <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-800/50 p-2 rounded-lg border border-slate-800">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>{formatDate(s.period_start)} to {formatDate(s.period_end)}</span>
              </div>

              {/* Financial Metrics */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Opening Balance</span>
                  <span className="font-mono text-slate-200 font-medium">
                    {formatCurrency(s.opening_balance)}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Closing Balance</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {formatCurrency(s.closing_balance)}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Credits (+)</span>
                  <span className="font-mono text-emerald-400">
                    {formatCurrency(s.total_credits)}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                  <span className="text-[10px] text-slate-500 block">Debits (-)</span>
                  <span className="font-mono text-rose-400">
                    {formatCurrency(s.total_debits)}
                  </span>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 flex justify-between items-center">
                <span>Transactions: <b className="text-slate-300 font-mono">{s.total_transactions}</b></span>
                <span>Parser: <b className="text-slate-300">{s.parser_used}</b></span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-1">
              <button
                onClick={() => onSelectStatement(s.id, 'transactions')}
                title="View Transactions Spreadsheet"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1 text-xs"
              >
                <Table className="w-3.5 h-3.5 text-blue-400" />
                <span>Rows</span>
              </button>
              <button
                onClick={() => onSelectStatement(s.id, 'analytics')}
                title="View Analytics"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1 text-xs"
              >
                <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
                <span>Analytics</span>
              </button>
              <button
                onClick={() => onSelectStatement(s.id, 'reconciliation')}
                title="View Reconciliation"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition flex items-center gap-1 text-xs"
              >
                <Scale className="w-3.5 h-3.5 text-amber-400" />
                <span>Recon</span>
              </button>
              <button
                onClick={() => handleExportExcel(s.id)}
                title="Export 13-Sheet CA Excel Analysis Workbook"
                className="p-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/40 border border-emerald-500/40 text-emerald-300 transition flex items-center gap-1.5 text-xs font-medium"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>Export Excel</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
