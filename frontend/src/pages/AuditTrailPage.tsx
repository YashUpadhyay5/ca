import React, { useState, useEffect } from 'react';
import { History, ShieldCheck, User, Clock, ArrowRight } from 'lucide-react';
import { AuditLogItem } from '../types';
import { apiClient } from '../api/client';
import { formatDate } from '../utils/formatters';

export const AuditTrailPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/audit/');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Immutable Audit Trail</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full forensic lineage of every extraction, manual edit, classification override, and verification
          </p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4" />
          <span>ICAI Tamper-Evident</span>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading audit records...</div>
      ) : logs.length === 0 ? (
        <div className="p-12 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-500 text-xs">
          No audit entries recorded yet. Actions such as document processing or manual edits will appear here.
        </div>
      ) : (
        <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Auditor / User</th>
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Entity</th>
                  <th className="px-6 py-3">Details / Value Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300 font-mono">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-6 py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td className="px-6 py-3.5 font-sans">
                      <div className="flex items-center gap-1.5 text-slate-200">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        <span>{log.user_email}</span>
                      </div>
                    </td>
                    <td className="px-6 py-3.5 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-300 border border-blue-500/20">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-slate-400 font-sans">
                      {log.entity_name} ({log.entity_id.slice(0, 8)}...)
                    </td>
                    <td className="px-6 py-3.5 font-sans">
                      <div className="text-slate-200">{log.details || '-'}</div>
                      {log.old_value && log.new_value && (
                        <div className="mt-1 p-2 rounded bg-slate-950 border border-slate-800 text-[10px] flex items-center gap-2 font-mono">
                          <span className="text-rose-400 truncate max-w-xs">
                            {JSON.stringify(log.old_value)}
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
                          <span className="text-emerald-400 truncate max-w-xs">
                            {JSON.stringify(log.new_value)}
                          </span>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
