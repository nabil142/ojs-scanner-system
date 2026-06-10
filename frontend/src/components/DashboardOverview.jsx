import React, { useEffect, useState } from 'react';
import { Shield, Clock, AlertTriangle, FileText, CheckCircle2, RefreshCw } from 'lucide-react';

export default function DashboardOverview() {
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [reportSummary, setReportSummary] = useState(null);
  const [targetInfo, setTargetInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    try {
      const normalizedDateStr = (dateStr.endsWith('Z') || dateStr.includes('+')) 
        ? dateStr 
        : `${dateStr}Z`;
      const d = new Date(normalizedDateStr);
      return d.toLocaleString('id-ID');
    } catch (e) {
      return dateStr;
    }
  };

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch scheduler status
      const schedulerRes = await fetch('http://127.0.0.1:8000/scheduler/status');
      const schedulerData = await schedulerRes.json();
      setSchedulerStatus(schedulerData);

      // 2. Fetch reports summary
      const reportsRes = await fetch('http://127.0.0.1:8000/reports/list');
      const reportsData = await reportsRes.json();
      setReportSummary(reportsData);

      // 3. Fetch target info
      const targetRes = await fetch('http://127.0.0.1:8000/scan/target-info');
      if (targetRes.ok) {
        const targetData = await targetRes.json();
        setTargetInfo(targetData);
      }
    } catch (err) {
      setError('Gagal mengambil data dari server backend API');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '200px' }}>
        <RefreshCw className="spinner" size={32} style={{ color: 'var(--color-accent)', marginBottom: '12px' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Memuat rangkuman keamanan...</p>
      </div>
    );
  }

  // Calculate some stats from the latest report if available
  const latestReport = reportSummary?.reports?.[0] || null;
  const totalReports = reportSummary?.total || 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 className="h1" style={{ marginBottom: 0 }}>Rangkuman Keamanan OJS</h1>
        <button className="btn btn-secondary" onClick={fetchData} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <RefreshCw size={14} /> Refresh Data
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: 'var(--radius-sm)',
          padding: '16px',
          color: 'var(--color-danger)',
          marginBottom: '24px'
        }}>
          {error}. Pastikan server backend Anda berjalan di port 8000.
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid-3">
        <div className="card" style={{ borderLeft: '4px solid var(--color-accent)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Total Pemindaian</p>
              <h3 style={{ fontSize: '32px', fontWeight: '700', color: '#fff' }}>{totalReports}</h3>
            </div>
            <div style={{ padding: '10px', backgroundColor: 'var(--color-accent-alpha)', borderRadius: '8px', color: 'var(--color-accent)' }}>
              <FileText size={20} />
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', marginTop: '12px' }}>
            Jumlah scan tersimpan di database
          </p>
        </div>

        <div className="card" style={{ borderLeft: `4px solid ${schedulerStatus?.running ? 'var(--color-success)' : 'var(--color-danger)'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Status Penjadwal</p>
              <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#fff', marginTop: '8px' }}>
                {schedulerStatus?.running ? 'AKTIF (6 Jam)' : 'NONAKTIF'}
              </h3>
            </div>
            <div style={{ 
              padding: '10px', 
              backgroundColor: schedulerStatus?.running ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
              borderRadius: '8px', 
              color: schedulerStatus?.running ? 'var(--color-success)' : 'var(--color-danger)' 
            }}>
              <Clock size={20} />
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', marginTop: '14px' }}>
            {schedulerStatus?.running ? `Scan berikutnya: ${schedulerStatus.jobs?.[0]?.next_run_time ? new Date(schedulerStatus.jobs[0].next_run_time).toLocaleString('id-ID') : '-'}` : 'Background scan dinonaktifkan'}
          </p>
        </div>

        <div className="card" style={{ borderLeft: '4px solid var(--color-info)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Scan Terakhir</p>
              <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#fff', marginTop: '12px', wordBreak: 'break-all' }}>
                {latestReport ? `${latestReport.target}` : 'Belum ada scan'}
              </h3>
            </div>
            <div style={{ padding: '10px', backgroundColor: 'rgba(6, 182, 212, 0.1)', borderRadius: '8px', color: 'var(--color-info)' }}>
              <Shield size={20} />
            </div>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', marginTop: '12px' }}>
            {latestReport ? `Dijalankan pada: ${formatDateTime(latestReport.timestamp)}` : 'Mulai lakukan pemindaian pertama Anda'}
          </p>
        </div>
      </div>

      <div style={{ marginTop: '24px' }}>
        {/* OJS Target Info Card */}
        <div className="card">
          <h2 className="h2" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={18} style={{ color: 'var(--color-accent)' }} /> Repositori Target OJS
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Source Path Default:</span>
              <span style={{ fontWeight: '600', fontSize: '14px', color: '#fff' }}>
                {targetInfo?.path || 'ojs/ojs-main'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Versi OJS:</span>
              <span style={{ fontWeight: '600', fontSize: '14px', color: '#fff' }}>
                {targetInfo?.version || 'Tidak terdeteksi'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Jumlah File Diperiksa:</span>
              <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--color-success)' }}>
                {targetInfo?.file_count !== undefined ? `${targetInfo.file_count} file` : '-'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Mekanisme Audit:</span>
              <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--color-success)' }}>
                Static Application Security Testing (SAST)
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Mesin Analisis:</span>
              <span style={{ fontWeight: '600', fontSize: '14px', color: 'var(--color-info)' }}>
                Regex AST Audit + Semgrep (Jika Aktif)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
