import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Edit2,
  Check,
  X,
  FileText,
  Search,
} from 'lucide-react';
import { ReviewItem, Statement } from '../types';
import { formatCurrency, formatDate } from '../utils/formatters';
import { apiClient } from '../api/client';

interface ReviewQueuePageProps {
  statements: Statement[];
  onRefreshReviewCount: () => void;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({
  statements,
  onRefreshReviewCount,
}) => {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeItem, setActiveItem] = useState<ReviewItem | null>(null);
  const [resolutionAction, setResolutionAction] = useState<string>('ACCEPT');
  const [resolutionNote, setResolutionNote] = useState<string>('');
  const [newCategory, setNewCategory] = useState<string>('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/review/');
      setItems(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleResolve = async () => {
    if (!activeItem) return;
    try {
      await apiClient.post(`/review/${activeItem.id}/resolve`, {
        action: resolutionAction,
        category: newCategory || undefined,
        resolution_note: resolutionNote,
      });
      setActiveItem(null);
      setResolutionNote('');
      fetchQueue();
      onRefreshReviewCount();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">CA Review & Verification Queue</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Human-in-the-loop audit verification for low confidence scores, duplicate suspicions, and balance breaks
          </p>
        </div>
        <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-xs font-bold">
          {items.length} Pending Actions
        </span>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading audit review items...</div>
      ) : items.length === 0 ? (
        <div className="p-12 rounded-xl bg-slate-900 border border-slate-800 text-center space-y-2">
          <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto" />
          <h3 className="text-base font-bold text-white">Review Queue is Clear!</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            All extracted transactions have satisfied the 90%+ confidence threshold and balance continuity equations.
          </p>
        </div>
      ) : (
        <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Date</th>
                  <th className="px-6 py-3">Issue Reason</th>
                  <th className="px-6 py-3">Narration</th>
                  <th className="px-6 py-3 text-right">Amount</th>
                  <th className="px-6 py-3 text-center">Confidence</th>
                  <th className="px-6 py-3 text-right">Review Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-3.5 text-slate-400 whitespace-nowrap">
                      {formatDate(item.date)}
                    </td>
                    <td className="px-6 py-3.5 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30">
                        {item.issue_code}
                      </span>
                      <div className="text-[11px] text-slate-400 mt-1 max-w-xs font-sans">
                        {item.issue_description}
                      </div>
                    </td>
                    <td className="px-6 py-3.5 font-sans">
                      <div className="text-white font-medium max-w-sm truncate">{item.narration}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        Category: {item.category} • Mode: {item.payment_mode}
                      </div>
                    </td>
                    <td className="px-6 py-3.5 text-right font-medium">
                      {item.debit_amount > 0 ? (
                        <span className="text-rose-400">{formatCurrency(item.debit_amount)}</span>
                      ) : (
                        <span className="text-emerald-400">{formatCurrency(item.credit_amount)}</span>
                      )}
                    </td>
                    <td className="px-6 py-3.5 text-center">
                      <span className="text-amber-400 font-bold">
                        {(item.confidence_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right font-sans">
                      <button
                        onClick={() => {
                          setActiveItem(item);
                          setResolutionAction('ACCEPT');
                          setNewCategory(item.category);
                          setResolutionNote('');
                        }}
                        className="px-3 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition"
                      >
                        Verify & Resolve
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Review Resolution Modal */}
      {activeItem && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Resolve Audit Flag
              </h3>
              <button onClick={() => setActiveItem(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/60">
                <div className="font-semibold text-amber-400">{activeItem.issue_code}</div>
                <div className="text-slate-300 mt-1">{activeItem.issue_description}</div>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Narration:</span>
                <div className="p-2.5 rounded bg-slate-800 text-slate-100">{activeItem.narration}</div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Decision / Action *:</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['ACCEPT', 'EDIT', 'REJECT'] as const).map((act) => (
                    <button
                      key={act}
                      type="button"
                      onClick={() => setResolutionAction(act)}
                      className={`py-2 rounded-lg font-semibold border transition ${
                        resolutionAction === act
                          ? 'bg-blue-600 text-white border-blue-500'
                          : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'
                      }`}
                    >
                      {act}
                    </button>
                  ))}
                </div>
              </div>

              {resolutionAction === 'EDIT' && (
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Correct Category:</label>
                  <input
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    placeholder="e.g. Business Expense, Tax, Salary"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Resolution Audit Note *:</label>
                <input
                  type="text"
                  required
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="e.g. Confirmed with client bank confirmation letter"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setActiveItem(null)}
                className="px-4 py-2 text-slate-400 hover:text-white text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-lg shadow-md transition"
              >
                Submit Verification
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
