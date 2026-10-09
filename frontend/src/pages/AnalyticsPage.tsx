import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Receipt,
  PieChart as PieIcon,
  CreditCard,
  Building,
  CheckCircle,
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import { Statement, FinancialOverview } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface AnalyticsPageProps {
  statements: Statement[];
  selectedStatementId: string | null;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({
  statements,
  selectedStatementId,
}) => {
  const [activeStatementId, setActiveStatementId] = useState<string>(
    selectedStatementId || statements[0]?.id || ''
  );
  const [analytics, setAnalytics] = useState<FinancialOverview | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    if (!activeStatementId) return;
    setLoading(true);
    try {
      const res = await apiClient.get(`/statements/${activeStatementId}/analytics`);
      setAnalytics(res.data);
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
    fetchAnalytics();
  }, [activeStatementId]);

  const COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#64748B'];

  return (
    <div className="space-y-6">
      {/* Statement Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Financial Intelligence & Tax Analytics</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Indian Financial Year Trends • Tax Deductions & Payments • Category Breakdown
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

      {loading || !analytics ? (
        <div className="p-12 text-center text-slate-400">Loading comprehensive financial analysis...</div>
      ) : (
        <>
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Average Transaction
              </span>
              <div className="text-xl font-bold text-white font-mono mt-2">
                {formatCurrency(analytics.average_transaction)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Median: {formatCurrency(analytics.median_transaction)}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Largest Debit Outflow
              </span>
              <div className="text-xl font-bold text-rose-400 font-mono mt-2">
                {formatCurrency(analytics.largest_debit)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Single highest expense</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Largest Credit Inflow
              </span>
              <div className="text-xl font-bold text-emerald-400 font-mono mt-2">
                {formatCurrency(analytics.largest_credit)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Single highest receipt</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Standard Deviation
              </span>
              <div className="text-xl font-bold text-blue-400 font-mono mt-2">
                {formatCurrency(analytics.std_dev_transaction)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">Cashflow volatility metric</div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Monthly Trend Chart (2 cols) */}
            <div className="lg:col-span-2 p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">Monthly Cashflow (Indian FY)</h3>
                  <p className="text-xs text-slate-400">Total Credits vs Total Debits by Month</p>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.monthly_trends}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="month_name" stroke="#94a3b8" fontSize={11} />
                    <YAxis
                      stroke="#94a3b8"
                      fontSize={11}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(val: any) => formatCurrency(val)}
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                    />
                    <Legend />
                    <Bar dataKey="credits" name="Credits (+)" fill="#10B981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="debits" name="Debits (-)" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Payment Mode Breakdown (1 col) */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white">Payment Mode Breakdown</h3>
                <p className="text-xs text-slate-400">Distribution by volume share</p>
              </div>

              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analytics.payment_modes}
                      dataKey="total_amount"
                      nameKey="mode"
                      cx="50%"
                      cy="50%"
                      outerRadius={75}
                      innerRadius={45}
                    >
                      {analytics.payment_modes.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val: any) => formatCurrency(val)}
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {analytics.payment_modes.map((pm, i) => (
                  <div key={i} className="flex justify-between items-center text-xs text-slate-300">
                    <span className="flex items-center gap-1.5">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                      />
                      {pm.mode} ({pm.count})
                    </span>
                    <span className="font-mono">{pm.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tax-Oriented Intelligence Section (Section 26) */}
          <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Receipt className="w-5 h-5 text-amber-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">Tax Intelligence & Statutory Payments</h3>
                  <p className="text-xs text-slate-400">
                    Automated detection of GST, TDS, and Advance Tax Challans (Suggested Classification — CA Verification Required)
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {analytics.tax_summary.map((t, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
                  <div className="text-xs font-semibold text-slate-400">{t.tax_type} Payments</div>
                  <div className="text-lg font-bold text-amber-400 font-mono mt-1">
                    {formatCurrency(t.total_paid)}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {t.transaction_count} transaction{t.transaction_count !== 1 ? 's' : ''} detected
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Debits & Credits */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top 10 Debits */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-rose-400" />
                Top 10 Debit Expenses
              </h3>
              <div className="space-y-2">
                {analytics.top_debits.slice(0, 5).map((t, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 flex justify-between items-center text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="font-semibold text-white truncate max-w-xs">{t.narration}</div>
                      <div className="text-slate-400 text-[11px]">
                        {formatDate(t.date)} • {t.category} • {t.payment_mode}
                      </div>
                    </div>
                    <div className="font-mono text-rose-400 font-bold">{formatCurrency(t.amount)}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top 10 Credits */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Top 10 Credit Inflows
              </h3>
              <div className="space-y-2">
                {analytics.top_credits.slice(0, 5).map((t, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-lg bg-slate-800/40 border border-slate-800 flex justify-between items-center text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="font-semibold text-white truncate max-w-xs">{t.narration}</div>
                      <div className="text-slate-400 text-[11px]">
                        {formatDate(t.date)} • {t.category} • {t.payment_mode}
                      </div>
                    </div>
                    <div className="font-mono text-emerald-400 font-bold">{formatCurrency(t.amount)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
