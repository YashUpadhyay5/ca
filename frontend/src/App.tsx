import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { UploadModal } from './components/upload/UploadModal';
import { AssistantDrawer } from './components/assistant/AssistantDrawer';
import { Dashboard } from './pages/Dashboard';
import { ClientsPage } from './pages/ClientsPage';
import { StatementsPage } from './pages/StatementsPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ReconciliationPage } from './pages/ReconciliationPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { LoginPage } from './pages/LoginPage';
import { Client, Statement } from './types';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('cafiniq_token'));
  const [user, setUser] = useState<any>(
    localStorage.getItem('cafiniq_user') ? JSON.parse(localStorage.getItem('cafiniq_user')!) : null
  );

  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [clients, setClients] = useState<Client[]>([]);
  const [statements, setStatements] = useState<Statement[]>([]);
  const [selectedStatementId, setSelectedStatementId] = useState<string | null>(null);
  const [reviewCount, setReviewCount] = useState<number>(0);

  // Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);

  const fetchData = async () => {
    if (!token) return;
    try {
      const [clientsRes, docsRes, reviewRes] = await Promise.all([
        apiClient.get('/clients/'),
        apiClient.get('/documents/'),
        apiClient.get('/review/'),
      ]);
      setClients(clientsRes.data);
      setReviewCount(reviewRes.data.length);

      // Fetch all statements directly
      try {
        const stmtsRes = await apiClient.get('/statements/');
        const stmtsList = stmtsRes.data || [];
        setStatements(stmtsList);
        if (stmtsList.length > 0 && !selectedStatementId) {
          setSelectedStatementId(stmtsList[0].id);
        }
      } catch (err) {
        setStatements([]);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  const handleLoginSuccess = (loggedInUser: any, jwtToken: string) => {
    setUser(loggedInUser);
    setToken(jwtToken);
    fetchData();
  };

  const handleLogout = () => {
    localStorage.removeItem('cafiniq_token');
    localStorage.removeItem('cafiniq_user');
    setToken(null);
    setUser(null);
  };

  const handleUploadComplete = async (statementId: string) => {
    await fetchData();
    setSelectedStatementId(statementId);
    setCurrentTab('transactions');
  };

  if (!token) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <Navbar
        user={user}
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenAssistant={() => setIsAssistantOpen(true)}
        onLogout={handleLogout}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          reviewCount={reviewCount}
        />

        {/* Main Workspace Viewport */}
        <main className="flex-1 overflow-y-auto p-6">
          {currentTab === 'dashboard' && (
            <Dashboard
              statements={statements}
              clients={clients}
              reviewCount={reviewCount}
              onSelectStatement={(id) => {
                setSelectedStatementId(id);
                setCurrentTab('transactions');
              }}
              onOpenUpload={() => setIsUploadOpen(true)}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'clients' && (
            <ClientsPage clients={clients} onRefresh={fetchData} />
          )}

          {currentTab === 'statements' && (
            <StatementsPage
              statements={statements}
              onSelectStatement={(id, tab) => {
                setSelectedStatementId(id);
                setCurrentTab(tab || 'transactions');
              }}
              onOpenUpload={() => setIsUploadOpen(true)}
            />
          )}

          {currentTab === 'transactions' && (
            <TransactionsPage
              statements={statements}
              selectedStatementId={selectedStatementId}
              onSelectStatementId={setSelectedStatementId}
            />
          )}

          {currentTab === 'analytics' && (
            <AnalyticsPage
              statements={statements}
              selectedStatementId={selectedStatementId}
            />
          )}

          {currentTab === 'reconciliation' && (
            <ReconciliationPage
              statements={statements}
              selectedStatementId={selectedStatementId}
            />
          )}

          {currentTab === 'review' && (
            <ReviewQueuePage
              statements={statements}
              onRefreshReviewCount={fetchData}
            />
          )}

          {currentTab === 'audit' && <AuditTrailPage />}
        </main>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        clients={clients}
        onUploadComplete={handleUploadComplete}
      />

      {/* Safe AI Natural Language Assistant Drawer */}
      <AssistantDrawer
        isOpen={isAssistantOpen}
        onClose={() => setIsAssistantOpen(false)}
        statementId={selectedStatementId}
      />
    </div>
  );
};

export default App;
