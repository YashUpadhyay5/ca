import React from 'react';
import { ShieldCheck, MessageSquareText, Upload, LogOut, Building2, User } from 'lucide-react';

interface NavbarProps {
  user: any;
  onOpenUpload: () => void;
  onOpenAssistant: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onOpenUpload, onOpenAssistant, onLogout }) => {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-blue-700 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <ShieldCheck className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            CaFinIQ <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/60 text-blue-300 font-mono border border-blue-700">v1.0 CA Edition</span>
          </h1>
          <p className="text-xs text-slate-400">Chartered Accountant Bank Statement Intelligence & Audit Platform</p>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Ask Assistant Button */}
        <button
          onClick={onOpenAssistant}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 flex items-center gap-2 transition"
        >
          <MessageSquareText className="w-4 h-4 text-blue-400" />
          <span>Ask Assistant</span>
        </button>

        {/* Upload Statement Button */}
        <button
          onClick={onOpenUpload}
          className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-md shadow-blue-600/30 flex items-center gap-2 transition"
        >
          <Upload className="w-4 h-4" />
          <span>Upload PDF Statement</span>
        </button>

        {/* User Profile */}
        <div className="pl-3 border-l border-slate-800 flex items-center space-x-3">
          <div className="text-right hidden sm:block">
            <div className="text-sm font-medium text-slate-200">{user?.full_name || 'CA Rajesh Mehta'}</div>
            <div className="text-xs text-emerald-400 font-mono">{user?.role || 'FCA / AUDITOR'}</div>
          </div>
          <button
            onClick={onLogout}
            title="Log Out"
            className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
