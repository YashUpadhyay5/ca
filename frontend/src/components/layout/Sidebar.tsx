import React from 'react';
import {
  LayoutDashboard,
  Users,
  FileSpreadsheet,
  TableProperties,
  BarChart3,
  Scale,
  AlertTriangle,
  History,
  FileDown
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  reviewCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, reviewCount }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'clients', label: 'Clients & Accounts', icon: Users },
    { id: 'statements', label: 'Bank Statements', icon: FileSpreadsheet },
    { id: 'transactions', label: 'Transaction Spreadsheet', icon: TableProperties },
    { id: 'analytics', label: 'Financial Analytics & Tax', icon: BarChart3 },
    { id: 'reconciliation', label: 'Reconciliation Studio', icon: Scale },
    { 
      id: 'review', 
      label: 'Review Queue', 
      icon: AlertTriangle,
      badge: reviewCount > 0 ? reviewCount : undefined
    },
    { id: 'audit', label: 'Audit Trail', icon: History },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between shrink-0 h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Audit Workspace
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 text-xs text-slate-400">
          <div className="font-semibold text-slate-300 mb-1">Standard ICAI Rules</div>
          <div>Balance Continuity: Active</div>
          <div>Decimal Mode: Precision (0.01)</div>
        </div>
      </div>
    </aside>
  );
};
