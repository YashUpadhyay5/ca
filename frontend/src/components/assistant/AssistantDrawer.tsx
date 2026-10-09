import React, { useState } from 'react';
import { X, Send, Bot, Sparkles, AlertCircle, ArrowUpRight } from 'lucide-react';
import { apiClient } from '../../api/client';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface AssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  statementId: string | null;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({
  isOpen,
  onClose,
  statementId,
}) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<any[]>([]);

  if (!isOpen) return null;

  const quickPrompts = [
    'Show all UPI payments above ₹10,000',
    'What was the largest debit transaction?',
    'How much was spent on Tax & GST?',
    'Find all transactions for Amazon',
  ];

  const handleAsk = async (textToAsk: string) => {
    if (!textToAsk.trim() || !statementId) return;

    const userMessage = { role: 'user', content: textToAsk };
    setChatHistory((prev) => [...prev, userMessage]);
    setLoading(true);
    setQuery('');

    try {
      const res = await apiClient.post('/assistant/query', {
        statement_id: statementId,
        query: textToAsk,
      });

      const assistantMessage = {
        role: 'assistant',
        content: res.data.answer,
        data: res.data,
      };
      setChatHistory((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Unable to evaluate query: ' + (err.response?.data?.detail || err.message),
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              Ask Your Bank Statement <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            </h3>
            <p className="text-xs text-slate-400">Strictly Calculated CA Assistant (No Hallucinations)</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg transition">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatHistory.length === 0 && (
          <div className="text-center py-8 space-y-4">
            <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-blue-400">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">What would you like to verify?</p>
              <p className="text-xs text-slate-400 mt-1">
                Every calculation is mathematically proved against database transactions.
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Quick Prompts
              </div>
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAsk(p)}
                  className="w-full text-left px-3 py-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-xs text-slate-300 hover:text-white transition flex items-center justify-between"
                >
                  <span>{p}</span>
                  <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
                </button>
              ))}
            </div>
          </div>
        )}

        {chatHistory.map((msg, i) => (
          <div
            key={i}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-none shadow-md'
              }`}
            >
              <p>{msg.content}</p>

              {/* Underlying Data Proof */}
              {msg.data?.applied_filters && msg.data.applied_filters.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-700 text-[10px] text-slate-400">
                  <div className="font-semibold text-slate-300">Applied Filters:</div>
                  <ul className="list-disc list-inside">
                    {msg.data.applied_filters.map((f: string, fi: number) => (
                      <li key={fi}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Sample transactions preview */}
              {msg.data?.transactions && msg.data.transactions.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
                  <div className="font-semibold text-[10px] text-slate-300">Sample Records:</div>
                  {msg.data.transactions.slice(0, 3).map((t: any, ti: number) => (
                    <div
                      key={ti}
                      className="p-1.5 rounded bg-slate-900/60 border border-slate-800 text-[10px] flex justify-between"
                    >
                      <span className="truncate max-w-[180px]">{t.narration}</span>
                      <span className="font-mono text-emerald-400">
                        {formatCurrency(t.debit > 0 ? t.debit : t.credit)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Bot className="w-4 h-4 text-blue-400 animate-bounce" />
            <span>Calculating structured answer...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAsk(query);
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={statementId ? 'Ask question about this statement...' : 'Select a statement first'}
            disabled={!statementId || loading}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={!statementId || loading || !query.trim()}
            className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
