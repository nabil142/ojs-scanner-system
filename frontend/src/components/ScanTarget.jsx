import React, { useState } from 'react';
import { Search, ShieldAlert, ShieldCheck, Download, ExternalLink, Loader2 } from 'lucide-react';
import { API_URL } from '../config';

export default function ScanTarget() {
  const [sourcePath, setSourcePath] = useState('');
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState('');

  const handleScan = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setScanResult(null);

    try {
      const res = await fetch(`${API_URL}/scan/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ internal_path: sourcePath })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan pada server saat memindai.');
      }

      setScanResult(data);
    } catch (err) {
      setError(err.message || 'Koneksi ke backend API terputus. Pastikan FastAPI berjalan.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate score and status
  const totalVulns = scanResult?.total_vulnerabilities || 0;
  const score = Math.max(0, 100 - (totalVulns * 15));
  
  let status = 'Safe';
  let statusColor = 'var(--color-success)';
  if (totalVulns > 0) {
    const hasCriticalOrHigh = scanResult?.vulnerabilities?.some(v => v.level === 'Critical' || v.level === 'High');
    if (hasCriticalOrHigh) {
      status = 'Critical';
      statusColor = 'var(--color-danger)';
    } else {
      status = 'Warning';
      statusColor = 'var(--color-warning)';
    }
  }

  const getBadgeClass = (level) => {
    const lvl = String(level || '').toLowerCase();
    if (lvl === 'critical') return 'badge-critical';
    if (lvl === 'high') return 'badge-high';
    if (lvl === 'medium') return 'badge-medium';
    return 'badge-low';
  };

  return (
    <div>
      <h1 className="h1">Pemindai Kode OJS (SAST)</h1>

      {/* Input Form Card */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <form onSubmit={handleScan} style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: '1', minWidth: '300px', marginBottom: 0 }}>
            <label>OJS Source Path</label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Contoh: /ojs atau ojs/ojs-main"
                value={sourcePath}
                onChange={(e) => setSourcePath(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary" style={{ padding: '12px 24px' }} disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={16} className="spinner" /> Memindai...
              </>
            ) : (
              <>
                <Search size={16} /> Jalankan Scan
              </>
            )}
          </button>
        </form>
        <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', marginTop: '12px' }}>
          *Isi path target OJS Anda di server. Jika dijalankan menggunakan Docker Compose, isi dengan <code>/ojs</code>.
        </p>
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
          {error}
        </div>
      )}

      {/* Loading State Animation */}
      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '48px 0', border: '1px dashed var(--color-accent)' }}>
          <Loader2 size={48} className="spinner" style={{ color: 'var(--color-accent)', margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }} className="pulse">Pemindaian Kode Sedang Berlangsung</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
            Harap tunggu. Agent SAST sedang melakukan analisis sintaksis statis dan pemeriksaan file pada direktori OJS (memerlukan waktu 15-20 detik).
          </p>
        </div>
      )}

      {/* Result UI */}
      {scanResult && (
        <div>
          {/* Result Summary Grid */}
          <div className="grid-3">
            <div className="card" style={{ borderLeft: '4px solid var(--color-accent)' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Total Kerentanan</p>
              <h3 style={{ fontSize: '32px', fontWeight: '700', color: '#fff' }}>{totalVulns}</h3>
            </div>
            
            <div className="card" style={{ borderLeft: `4px solid ${statusColor}` }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Skor Keamanan</p>
              <h3 style={{ fontSize: '32px', fontWeight: '700', color: '#fff' }}>{scanResult.target_valid ? score : '-'}</h3>
            </div>

            <div className="card" style={{ borderLeft: `4px solid ${statusColor}` }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '4px' }}>Status</p>
              <h3 style={{ fontSize: '28px', fontWeight: '700', color: statusColor, marginTop: '4px' }}>
                {scanResult.target_valid ? status : 'Invalid Target'}
              </h3>
            </div>
          </div>

          {/* Action Buttons for Reports */}
          {scanResult.target_valid && (
            <div style={{ display: 'flex', gap: '12px', marginBottom: '32px' }}>
              {scanResult.history_id && (
                <>
                  <a 
                    href={`${API_URL}/scan/report/${scanResult.history_id}`} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="btn btn-secondary"
                    style={{ textDecoration: 'none' }}
                  >
                    <Download size={14} /> Download PDF Report
                  </a>
                  <a 
                    href={`${API_URL}/reports/${scanResult.history_id}/html`} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="btn btn-primary"
                    style={{ textDecoration: 'none' }}
                  >
                    <ExternalLink size={14} /> Lihat Laporan HTML
                  </a>
                </>
              )}
            </div>
          )}

          {/* Repository target metadata */}
          {scanResult.repository_status && (
            <div className="card" style={{ marginBottom: '32px' }}>
              <h3 className="h3" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '8px', marginBottom: '16px' }}>Detail Target Repository</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '14px' }}>
                <div>
                  <span style={{ color: 'var(--text-secondary)' }}>Status Deteksi: </span>
                  <span style={{ fontWeight: '600', color: scanResult.repository_status.is_ojs ? 'var(--color-success)' : 'var(--color-danger)' }}>
                    {scanResult.repository_status.status || '-'}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-secondary)' }}>Versi OJS: </span>
                  <span style={{ fontWeight: '600', color: '#fff' }}>{scanResult.repository_status.version || '-'}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-secondary)' }}>File Versi: </span>
                  <span style={{ fontWeight: '600', color: 'var(--text-secondary)' }}>{scanResult.repository_status.version_source || '-'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Vulnerability Table Card */}
          <div className="card">
            <h2 className="h2" style={{ marginBottom: '20px' }}>Daftar Kerentanan yang Ditemukan</h2>
            {totalVulns === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-secondary)' }}>
                {scanResult.target_valid ? (
                  <>
                    <ShieldCheck size={40} style={{ color: 'var(--color-success)', marginBottom: '12px' }} />
                    <p style={{ fontWeight: '600', color: '#fff' }}>Tidak Ditemukan Kerentanan!</p>
                    <p style={{ fontSize: '13px' }}>Kode OJS Anda bersih dari celah keamanan yang terdefinisi.</p>
                  </>
                ) : (
                  <p>{scanResult.message || 'Path OJS yang diinput tidak valid. Silakan periksa kembali path direktori Anda.'}</p>
                )}
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Jenis Celah</th>
                      <th>Severity</th>
                      <th>Skor</th>
                      <th>Lokasi File</th>
                      <th>Kode Bermasalah</th>
                      <th>Rekomendasi Perbaikan</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scanResult.vulnerabilities?.map((vuln, index) => (
                      <tr key={index}>
                        <td style={{ fontWeight: '600', fontSize: '13.5px', color: '#fff' }}>{vuln.type || vuln.vulnerability_type}</td>
                        <td>
                          <span className={`badge ${getBadgeClass(vuln.level || vuln.severity)}`}>
                            {vuln.level || vuln.severity}
                          </span>
                        </td>
                        <td style={{ fontWeight: '600' }}>{vuln.score}</td>
                        <td style={{ fontSize: '12.5px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                          {vuln.location || vuln.file_path}
                        </td>
                        <td>
                          <code style={{
                            display: 'block',
                            backgroundColor: 'var(--bg-primary)',
                            padding: '8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            color: '#fcd34d',
                            fontFamily: 'monospace',
                            whiteSpace: 'pre-wrap',
                            maxWidth: '300px',
                            overflowX: 'auto'
                          }}>
                            {vuln.code_snippet || vuln.vulnerable_code || '-'}
                          </code>
                        </td>
                        <td style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '300px' }}>
                          {vuln.repair_steps || vuln.recommendation}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
