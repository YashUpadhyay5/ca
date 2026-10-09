import React, { useState, useEffect } from 'react';
import {
  Scale,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRightLeft,
  Building,
  RefreshCw,
} from 'lucide-react';
import { Statement, ReconciliationReport } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface ReconciliationPageProps {
  statements: Statement[];
  selectedStatementId: string | null;
}

export const ReconciliationPage: React.FC<ReconciliationPageProps> = ({
  statements,
  selectedStatementId,
}) => {
  const [activeStatementId, setActiveStatementId] = useState<string>(
    selectedStatementId || statements[0]?.id || ''
  );
  const [report, setReport] = useState<ReconciliationReport | null>(null);
  const [loading, setLoading] = useState(false);

  // Multi-account consolidation state
  const [selectedConsolidationIds, setSelectedConsolidationIds] = useState<string[]>([]);
  const [consolidationResult, setConsolidationResult] = useState<any>(null);
  const [consolidating, setConsolidating] = useState(false);

  const fetchReconciliation = async () => {
    if (!activeStatementId) return;
    setLoading(true);
    try {
      const res = await apiClient.get(`/statements/${activeStatementId}/reconciliation`);
      setReport(res.data);
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
    fetchReconciliation();
  }, [activeStatementId]);

  const handleRunConsolidation = async () => {
    if (selectedConsolidationIds.length === 0) return;
    setConsolidating(true);
    try {
      const res = await apiClient.post('/statements/consolidate', {
        statement_ids: selectedConsolidationIds,
      });
      setConsolidationResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setConsolidating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Reconciliation Studio</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Step-by-Step Balance Continuity Verification & Multi-Account Consolidation
          </p>
        </div>
        <select
          value={activeStatementId}
          onChange={(e) => setActiveStatementId(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-64"
        >
          {statements.map((s) => (
            <option key={s.id} value={s.id}>
              {s.bank_name} ({s.account_number_detected || 'Masked'})
            </option>
          ))}
        </select>
      </div>

      {loading || !report ? (
        <div className="p-12 text-center text-slate-400">Verifying balance continuity equations...</div>
      ) : (
        <>
          {/* Statement Reconciliation Equation Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-sm space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div
                  className={`p-3 rounded-xl border ${
                    report.status === 'RECONCILED'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                  }`}
                >
                  <Scale className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Statement Reconciliation Proof</h3>
                  <div className="text-xs text-slate-400">
                    Formula: Opening Balance + Total Credits - Total Debits = Expected Closing Balance
                  </div>
                </div>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold font-mono tracking-wide ${
                  report.status === 'RECONCILED'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                }`}
              >
                {report.status}
              </span>
            </div>

            {/* Invariant Equation Flow */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
              <div className="p-3.5 bg-slate-800/50 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Opening Balance
                </span>
                <span className="text-sm font-bold text-slate-200 font-mono mt-1 block">
                  {formatCurrency(report.opening_balance)}
                </span>
              </div>

              <div className="p-3.5 bg-slate-800/50 rounded-xl border border-slate-800">
                <span className="text-[10px] text-emerald-400 font-semibold uppercase block">
                  Credits (+)
                </span>
                <span className="text-sm font-bold text-emerald-400 font-mono mt-1 block">
                  {formatCurrency(report.sum_credits)}
                </span>
              </div>

              <div className="p-3.5 bg-slate-800/50 rounded-xl border border-slate-800">
                <span className="text-[10px] text-rose-400 font-semibold uppercase block">
                  Debits (-)
                </span>
                <span className="text-sm font-bold text-rose-400 font-mono mt-1 block">
                  {formatCurrency(report.sum_debits)}
                </span>
              </div>

              <div className="p-3.5 bg-slate-800/50 rounded-xl border border-slate-800">
                <span className="text-[10px] text-blue-400 font-semibold uppercase block">
                  Expected Closing
                </span>
                <span className="text-sm font-bold text-blue-400 font-mono mt-1 block">
                  {formatCurrency(report.expected_closing_balance)}
                </span>
              </div>

              <div className="p-3.5 bg-slate-800/50 rounded-xl border border-slate-800">
                <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                  Discrepancy
                </span>
                <span
                  className={`text-sm font-bold font-mono mt-1 block ${
                    report.discrepancy === 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {formatCurrency(report.discrepancy)}
                </span>
              </div>
            </div>
          </div>

          {/* Step-by-Step Continuity Audit */}
          <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Step-by-Step Balance Continuity Log</h3>
                <p className="text-xs text-slate-400">
                  Verifies that each transaction row mathematically steps into the next running balance
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Broken Steps: <b className="text-amber-400">{report.broken_step_count}</b>
              </span>
            </div>

            {report.broken_steps.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400 space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                <div className="text-white font-semibold">100% Mathematical Continuity Verified</div>
                <p className="text-slate-500 max-w-sm mx-auto">
                  Every single transaction row matches the reported running balance within 0.05 rounding tolerance.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Row</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Narration</th>
                      <th className="px-4 py-3 text-right">Debit</th>
                      <th className="px-4 py-3 text-right">Credit</th>
                      <th className="px-4 py-3 text-right">Expected Bal</th>
                      <th className="px-4 py-3 text-right">Reported Bal</th>
                      <th className="px-4 py-3 text-right">Variance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 font-mono text-slate-300">
                    {report.broken_steps.map((step, idx) => (
                      <tr key={idx} className="bg-rose-500/5 hover:bg-rose-500/10">
                        <td className="px-4 py-2.5 font-bold text-rose-400">{step.row_index}</td>
                        <td className="px-4 py-2.5 text-slate-400">{step.date}</td>
                        <td className="px-4 py-2.5 font-sans max-w-xs truncate text-white">
                          {step.narration}
                        </td>
                        <td className="px-4 py-2.5 text-right text-rose-400">
                          {step.debit > 0 ? formatCurrency(step.debit) : '-'}
                        </td>
                        <td className="px-4 py-2.5 text-right text-emerald-400">
                          {step.credit > 0 ? formatCurrency(step.credit) : '-'}
                        </td>
                        <td className="px-4 py-2.5 text-right text-blue-400 font-semibold">
                          {formatCurrency(step.expected_balance)}
                        </td>
                        <td className="px-4 py-2.5 text-right text-slate-300">
                          {formatCurrency(step.reported_balance)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-bold text-rose-400">
                          {formatCurrency(step.difference)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Multi-Account Consolidation Tool (Section 31) */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <div>
                <h3 className="text-base font-bold text-white">Multi-Account Consolidation & Internal Transfers</h3>
                <p className="text-xs text-slate-400">
                  Consolidate multiple statements for a client and eliminate reciprocal internal transfers to avoid double-counting.
                </p>
              </div>
            </div>

            <div className="p-4 bg-slate-800/40 rounded-xl border border-slate-700/60 space-y-3">
              <label className="text-xs font-semibold text-slate-300 block">
                Select Statements to Consolidate:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {statements.map((s) => {
                  const isChecked = selectedConsolidationIds.includes(s.id);
                  return (
                    <label
                      key={s.id}
                      className={`p-3 rounded-lg border flex items-center space-x-3 cursor-pointer transition text-xs ${
                        isChecked
                          ? 'border-blue-500 bg-blue-600/10 text-white'
                          : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-white'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {
                          setSelectedConsolidationIds((prev) =>
                            isChecked ? prev.filter((id) => id !== s.id) : [...prev, s.id]
                          );
                        }}
                        className="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0"
                      />
                      <div>
                        <div className="font-semibold">{s.bank_name}</div>
                        <div className="font-mono text-[10px] text-slate-500">
                          {s.account_number_detected || 'Masked'} • {s.total_transactions} txns
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  onClick={handleRunConsolidation}
                  disabled={selectedConsolidationIds.length < 2 || consolidating}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-semibold shadow-md transition flex items-center gap-2"
                >
                  <ArrowRightLeft className="w-4 h-4" />
                  <span>Consolidate Accounts</span>
                </button>
              </div>
            </div>

            {/* Consolidation Results */}
            {consolidationResult && (
              <div className="p-4 bg-slate-800/60 rounded-xl border border-blue-500/30 space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                  <div className="p-3 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Combined Credits</span>
                    <span className="text-sm font-bold text-emerald-400 font-mono mt-1 block">
                      {formatCurrency(consolidationResult.combined_credits)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Combined Debits</span>
                    <span className="text-sm font-bold text-rose-400 font-mono mt-1 block">
                      {formatCurrency(consolidationResult.combined_debits)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Net Movement</span>
                    <span className="text-sm font-bold text-blue-400 font-mono mt-1 block">
                      {formatCurrency(consolidationResult.net_movement)}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-amber-400 uppercase font-semibold block">Internal Transfers</span>
                    <span className="text-sm font-bold text-amber-400 font-mono mt-1 block">
                      {consolidationResult.detected_internal_transfers_count} pairs ({formatCurrency(consolidationResult.internal_transfers_volume)})
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
