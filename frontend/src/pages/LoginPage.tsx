import React, { useState } from 'react';
import { ShieldCheck, Lock, Mail, Building, ArrowRight, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';

interface LoginPageProps {
  onLoginSuccess: (user: any, token: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('ca@mehtaca.com');
  const [password, setPassword] = useState('AuditPassword123!');
  const [fullName, setFullName] = useState('CA Rajesh Mehta, FCA');
  const [orgName, setOrgName] = useState('K. R. Mehta & Associates, Chartered Accountants');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage(null);

    try {
      if (isRegister) {
        const res = await apiClient.post('/auth/register', {
          email,
          password,
          full_name: fullName,
          org_name: orgName,
          role: 'ADMIN',
        });
        localStorage.setItem('cafiniq_token', res.data.access_token);
        localStorage.setItem('cafiniq_user', JSON.stringify(res.data.user));
        onLoginSuccess(res.data.user, res.data.access_token);
      } else {
        const res = await apiClient.post('/auth/login', {
          email,
          password,
        });
        localStorage.setItem('cafiniq_token', res.data.access_token);
        localStorage.setItem('cafiniq_user', JSON.stringify(res.data.user));
        onLoginSuccess(res.data.user, res.data.access_token);
      }
    } catch (err: any) {
      setErrorMessage(
        err.response?.data?.detail || err.message || 'Authentication failed. Please verify credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      {/* Container */}
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl p-8 space-y-6">
        {/* Brand */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-700 to-indigo-600 flex items-center justify-center mx-auto shadow-lg shadow-blue-500/25">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">CaFinIQ</h1>
          <p className="text-xs text-slate-400">
            Enterprise Bank Statement Intelligence & Audit Platform for Indian CA Firms
          </p>
        </div>

        {/* Fast Login Notice */}
        <div className="p-3.5 bg-blue-950/40 border border-blue-800/40 rounded-xl text-xs text-blue-200 space-y-1">
          <div className="font-semibold text-blue-300 flex items-center gap-1.5">
            <span>CA Firm Credentials Pre-Configured</span>
          </div>
          <div className="text-[11px] text-blue-300/80">
            Click "Sign In" to access the platform, upload bank statement PDFs, and export 13-sheet CA analysis workbooks.
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {isRegister && (
            <>
              <div>
                <label className="block text-slate-400 font-semibold mb-1">CA Firm / Practice Name</label>
                <div className="relative">
                  <Building className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    required
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Your Full Name & Designation</label>
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-semibold mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {errorMessage && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-sm shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2 transition"
          >
            <span>{loading ? 'Authenticating...' : isRegister ? 'Register Firm & Account' : 'Sign In as CA'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Toggle Register / Login */}
        <div className="text-center pt-2">
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setErrorMessage(null);
            }}
            className="text-xs text-blue-400 hover:text-blue-300 transition"
          >
            {isRegister ? 'Already registered? Sign In' : 'New CA practice? Register your Firm'}
          </button>
        </div>
      </div>
    </div>
  );
};
