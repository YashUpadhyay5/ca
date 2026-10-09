import React, { useState } from 'react';
import {
  Upload,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  ArrowRight,
  FileSpreadsheet,
  Lock,
  Eye,
  EyeOff,
  HelpCircle,
  KeyRound,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { Client } from '../../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  clients: Client[];
  onUploadComplete: (statementId: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  clients,
  onUploadComplete,
}) => {
  const [selectedClientId, setSelectedClientId] = useState<string>(clients[0]?.id || '');
  const [customClientName, setCustomClientName] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [pdfPassword, setPdfPassword] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isPasswordRequired, setIsPasswordRequired] = useState<boolean>(false);
  const [pendingDocId, setPendingDocId] = useState<string | null>(null);
  const [showBankHints, setShowBankHints] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [progressPct, setProgressPct] = useState<number>(0);
  const [jobStats, setJobStats] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [completedStatementId, setCompletedStatementId] = useState<string | null>(null);
  const [isExportingExcel, setIsExportingExcel] = useState(false);

  if (!isOpen) return null;

  const resetState = () => {
    setFile(null);
    setPdfPassword('');
    setShowPassword(false);
    setIsPasswordRequired(false);
    setPendingDocId(null);
    setShowBankHints(false);
    setIsProcessing(false);
    setCurrentStep('');
    setProgressPct(0);
    setJobStats(null);
    setErrorMessage(null);
    setCompletedStatementId(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.name.toLowerCase().endsWith('.pdf')) {
        setFile(dropped);
        setErrorMessage(null);
        setIsPasswordRequired(false);
      } else {
        setErrorMessage('Please upload a valid PDF bank statement file.');
      }
    }
  };

  // 1. Initial Upload & Trigger
  const handleStartProcessing = async () => {
    if (!file) return;

    setIsProcessing(true);
    setErrorMessage(null);
    setCurrentStep('Uploading bank statement PDF...');
    setProgressPct(10);
    setCompletedStatementId(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (selectedClientId) {
        formData.append('client_id', selectedClientId);
      }
      if (customClientName.trim()) {
        formData.append('client_name', customClientName.trim());
      }
      if (pdfPassword.trim()) {
        formData.append('password', pdfPassword.trim());
      }

      // 1. Upload Document
      const uploadRes = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const docId = uploadRes.data.document_id;
      setPendingDocId(docId);

      // 2. Check if password is required
      if (uploadRes.data.password_required) {
        setIsProcessing(false);
        setIsPasswordRequired(true);
        setCurrentStep('');
        setErrorMessage('This PDF is password-protected. Please enter the statement password below to decrypt.');
        return;
      }

      // 3. Trigger processing pipeline
      await runProcessingJob(docId, pdfPassword.trim() || undefined);
    } catch (err: any) {
      setIsProcessing(false);
      setErrorMessage(err.response?.data?.detail || err.message || 'Upload failed.');
    }
  };

  // 2. Trigger Extraction Worker with Password
  const runProcessingJob = async (docId: string, passwordToUse?: string) => {
    setIsProcessing(true);
    setErrorMessage(null);
    setCurrentStep('Detecting bank layout & authenticating document...');
    setProgressPct(20);

    try {
      const payload: any = {};
      if (passwordToUse) {
        payload.password = passwordToUse;
      }

      const processRes = await apiClient.post(`/documents/${docId}/process`, payload);
      const jobId = processRes.data.job_id;

      // Poll extraction job
      const interval = setInterval(async () => {
        try {
          const pollRes = await apiClient.get(`/documents/jobs/${jobId}`);
          const job = pollRes.data;

          setCurrentStep(job.current_step);
          setProgressPct(job.progress_percentage);
          setJobStats(job);

          if (job.status === 'COMPLETED') {
            clearInterval(interval);
            setIsProcessing(false);
            setIsPasswordRequired(false);
            if (job.statement_id) {
              setCompletedStatementId(job.statement_id);
              onUploadComplete(job.statement_id);
            }
          } else if (job.status === 'FAILED') {
            clearInterval(interval);
            setIsProcessing(false);
            if (job.error_code === 'PASSWORD_REQUIRED' || job.error_code === 'INVALID_PASSWORD') {
              setIsPasswordRequired(true);
              setErrorMessage(job.error_message || 'Incorrect password. Please verify and try again.');
            } else {
              setErrorMessage(job.error_message || 'Processing failed.');
            }
          }
        } catch (err: any) {
          clearInterval(interval);
          setIsProcessing(false);
          setErrorMessage(err.message || 'Worker communication failed.');
        }
      }, 900);
    } catch (err: any) {
      setIsProcessing(false);
      const msg = err.response?.data?.detail || err.message || 'Processing initialization failed.';
      if (msg.toLowerCase().includes('password')) {
        setIsPasswordRequired(true);
      }
      setErrorMessage(msg);
    }
  };

  const handleUnlockAndProcess = async () => {
    if (!pendingDocId || !pdfPassword.trim()) {
      setErrorMessage('Please enter the statement password.');
      return;
    }
    await runProcessingJob(pendingDocId, pdfPassword.trim());
  };

  const handleDownloadExcel = async () => {
    if (!completedStatementId) return;
    setIsExportingExcel(true);
    try {
      const response = await apiClient.post(
        '/exports/excel',
        { statement_id: completedStatementId },
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Bank_Statement_Analysis_${completedStatementId.slice(0, 8)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download failed', err);
    } finally {
      setIsExportingExcel(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Upload className="w-5 h-5 text-blue-500" />
            <h2 className="text-base font-bold text-white">Upload Bank Statement PDF</h2>
          </div>
          {!isProcessing && (
            <button onClick={handleClose} className="text-slate-400 hover:text-white transition">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          {/* SUCCESS SCREEN */}
          {completedStatementId ? (
            <div className="space-y-5 text-center py-4">
              <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Statement Processed & Audited Successfully!</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Extracted {jobStats?.transactions_extracted || 0} transactions with ICAI balance reconciliation.
                </p>
              </div>

              {/* Extraction Metrics */}
              <div className="grid grid-cols-3 gap-2 bg-slate-800/60 p-3.5 rounded-xl border border-slate-700/50">
                <div>
                  <div className="text-[11px] text-slate-400">Transactions</div>
                  <div className="text-base font-bold text-white font-mono mt-0.5">
                    {jobStats?.transactions_extracted || 0}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-slate-400">Pages</div>
                  <div className="text-base font-bold text-white font-mono mt-0.5">
                    {jobStats?.pages_processed || 1}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] text-slate-400">Confidence</div>
                  <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                    {jobStats?.high_confidence_pct || 100}%
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={handleDownloadExcel}
                  disabled={isExportingExcel}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-600/30 transition flex items-center justify-center gap-2"
                >
                  {isExportingExcel ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <FileSpreadsheet className="w-4 h-4" />
                  )}
                  <span>Download Excel (.xlsx)</span>
                </button>
                <button
                  onClick={handleClose}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-600/20 transition flex items-center justify-center gap-1.5"
                >
                  <span>View Transactions</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : isPasswordRequired ? (
            /* PASSWORD REQUIRED PROMPT SCREEN */
            <div className="space-y-4 py-2">
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
                <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg shrink-0 mt-0.5">
                  <Lock className="w-5 h-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-amber-300">Statement is Password-Protected</h4>
                  <p className="text-xs text-amber-200/80">
                    Your bank encrypted this statement. Enter the password to decrypt and convert to Excel.
                  </p>
                </div>
              </div>

              {/* Password Input Box */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Enter Statement Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={pdfPassword}
                    onChange={(e) => {
                      setPdfPassword(e.target.value);
                      setErrorMessage(null);
                    }}
                    placeholder="e.g. Last 5 digits mobile + DDMM, PAN, or Cust ID"
                    disabled={isProcessing}
                    autoFocus
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3.5 py-2.5 pr-10 text-xs focus:outline-none focus:border-amber-500 font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-200 transition"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Bank Password Helper Accordion */}
              <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-3 space-y-2 text-xs">
                <button
                  type="button"
                  onClick={() => setShowBankHints(!showBankHints)}
                  className="flex items-center justify-between w-full text-slate-300 font-medium hover:text-white transition"
                >
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <KeyRound className="w-3.5 h-3.5" />
                    <span>Common Indian Bank Password Formats</span>
                  </span>
                  <span className="text-[11px] text-slate-400">{showBankHints ? 'Hide Hints ▲' : 'Show Hints ▼'}</span>
                </button>

                {showBankHints && (
                  <div className="pt-2 border-t border-slate-700/60 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-400">
                    <div>
                      <span className="text-white font-semibold">SBI:</span> Last 5 digits mobile + DOB (<code className="text-amber-300">DDMM</code>)
                    </div>
                    <div>
                      <span className="text-white font-semibold">HDFC:</span> Customer ID or Name + DOB (<code className="text-amber-300">DDMM</code>)
                    </div>
                    <div>
                      <span className="text-white font-semibold">ICICI:</span> First 4 letters Name + DOB (<code className="text-amber-300">DDMM</code>)
                    </div>
                    <div>
                      <span className="text-white font-semibold">Axis:</span> First 4 letters Name (UPPER) + Mobile last 4
                    </div>
                    <div>
                      <span className="text-white font-semibold">Kotak:</span> Customer CRN or DOB (<code className="text-amber-300">DDMMYYYY</code>)
                    </div>
                    <div>
                      <span className="text-white font-semibold">General:</span> Client PAN Card (<code className="text-amber-300">ABCDE1234F</code>)
                    </div>
                  </div>
                )}
              </div>

              {/* Error notice */}
              {errorMessage && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Unlock Actions */}
              <div className="pt-2 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsPasswordRequired(false)}
                  disabled={isProcessing}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleUnlockAndProcess}
                  disabled={isProcessing || !pdfPassword.trim()}
                  className="px-5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-amber-600/20 transition"
                >
                  {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  <span>Unlock & Process Statement</span>
                </button>
              </div>
            </div>
          ) : (
            /* STANDARD UPLOAD SCREEN */
            <>
              {/* Client Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Client / Taxpayer Name
                </label>
                {clients.length > 0 ? (
                  <select
                    value={selectedClientId}
                    onChange={(e) => setSelectedClientId(e.target.value)}
                    disabled={isProcessing}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:border-blue-500"
                  >
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name} {c.pan ? `(${c.pan})` : ''}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={customClientName}
                    onChange={(e) => setCustomClientName(e.target.value)}
                    placeholder="Enter Client Name (or leave blank to auto-detect from statement header)"
                    disabled={isProcessing}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3.5 py-2.5 text-xs focus:outline-none focus:border-blue-500 placeholder-slate-500"
                  />
                )}
                <p className="text-[11px] text-slate-500 mt-1">
                  Bank, account number, and holder name will be automatically detected from the statement.
                </p>
              </div>

              {/* Drag & Drop Zone */}
              {!isProcessing ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                      Bank Statement File
                    </label>
                    <div
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={handleFileDrop}
                      className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer ${
                        file
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-slate-700 hover:border-slate-600 bg-slate-800/40'
                      }`}
                      onClick={() => document.getElementById('pdf-file-input')?.click()}
                    >
                      <input
                        id="pdf-file-input"
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files && e.target.files[0]) {
                            setFile(e.target.files[0]);
                            setErrorMessage(null);
                          }
                        }}
                      />
                      <FileText className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                      {file ? (
                        <div>
                          <div className="text-sm font-semibold text-white">{file.name}</div>
                          <div className="text-xs text-slate-400 mt-1">
                            {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className="text-sm font-semibold text-slate-200">
                            Drag & Drop statement PDF here, or <span className="text-blue-400">Browse</span>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">
                            Supports Digital & Scanned statements (SBI, HDFC, ICICI, Axis, Kotak, Canara, etc.)
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Optional Upfront Password Input */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1 flex items-center justify-between">
                      <span className="flex items-center gap-1 text-slate-300">
                        <Lock className="w-3.5 h-3.5 text-slate-400" />
                        <span>PDF Password (Optional)</span>
                      </span>
                      <span className="text-[10px] text-slate-500 lowercase">Leave blank if not protected</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={pdfPassword}
                        onChange={(e) => setPdfPassword(e.target.value)}
                        placeholder="Enter password if file is protected (or you will be prompted automatically)"
                        disabled={isProcessing}
                        className="w-full bg-slate-800/80 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 pr-9 text-xs focus:outline-none focus:border-blue-500 font-mono placeholder-slate-500"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-2 text-slate-400 hover:text-slate-200 transition"
                      >
                        {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Live Processing Status */
                <div className="space-y-4 py-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-semibold text-slate-200 flex items-center gap-2">
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      {currentStep}
                    </span>
                    <span className="font-mono text-blue-400 font-bold">{progressPct}%</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>

                  {/* Real-time metrics */}
                  {jobStats && (
                    <div className="grid grid-cols-3 gap-2 pt-3">
                      <div className="p-2.5 bg-slate-800/70 rounded-lg text-center border border-slate-700/50">
                        <div className="text-xs text-slate-400">Pages</div>
                        <div className="text-base font-bold text-white font-mono">
                          {jobStats.pages_processed || 1}
                        </div>
                      </div>
                      <div className="p-2.5 bg-slate-800/70 rounded-lg text-center border border-slate-700/50">
                        <div className="text-xs text-slate-400">Transactions</div>
                        <div className="text-base font-bold text-emerald-400 font-mono">
                          {jobStats.transactions_extracted || 0}
                        </div>
                      </div>
                      <div className="p-2.5 bg-slate-800/70 rounded-lg text-center border border-slate-700/50">
                        <div className="text-xs text-slate-400">Confidence</div>
                        <div className="text-base font-bold text-blue-400 font-mono">
                          {jobStats.high_confidence_pct || 100}%
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Error notice */}
              {errorMessage && (
                <div className="p-3.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer (for regular upload screen) */}
        {!completedStatementId && !isPasswordRequired && (
          <div className="px-6 py-4 border-t border-slate-800 bg-slate-900/50 flex justify-end space-x-3">
            {!isProcessing && (
              <>
                <button
                  onClick={handleClose}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleStartProcessing}
                  disabled={!file}
                  className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-blue-600/20 transition"
                >
                  <span>Start Extraction & Audit Pipeline</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
