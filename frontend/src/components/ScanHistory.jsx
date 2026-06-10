import React, { useEffect, useState } from 'react';
import { FileText, Download, ExternalLink, Calendar, ChevronDown, ChevronUp, RefreshCw, AlertCircle } from 'lucide-react';
import { API_URL } from '../config';

export default function ScanHistory() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedRow, setExpandedRow] = useState(null);
  const [detailsCache, setDetailsCache] = useState({});
  const [detailsLoading, setDetailsLoading] = useState({});

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/reports/list`);
      const data = await res.json();
      if (data.status === 'success') {
        setReports(data.reports || []);
      } else {
        throw new Error('Gagal memproses daftar laporan.');
      }
    } catch (err) {
      setError('Koneksi backend gagal. Pastikan API server aktif.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const toggleRow = async (id) => {
    if (expandedRow === id) {
      setExpandedRow(null);
      return;
    }

    setExpandedRow(id);

    // Fetch details if not in cache
    if (!detailsCache[id]) {
      setDetailsLoading(prev => ({ ...prev, [id]: true }));
      try {
        const res = await fetch(`${API_URL}/reports/${id}/info`);
        const data = await res.json();
        setDetailsCache(prev => ({ ...prev, [id]: data }));
      } catch (err) {
        console.error('Failed to load report details:', err);
      } finally {
        setDetailsLoading(prev => ({ ...prev, [id]: false }));
      }
    }
  };

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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 className="h1" style={{ marginBottom: 0 }}>Riwayat Pemindaian</h1>
        <button className="btn btn-secondary" onClick={fetchHistory} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <RefreshCw size={14} /> Refresh Riwayat
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
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '200px' }}>
          <RefreshCw className="spinner" size={32} style={{ color: 'var(--color-accent)', marginBottom: '12px' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Memuat riwayat scan...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-secondary)' }}>
          <AlertCircle size={36} style={{ color: 'var(--text-muted)', marginBottom: '12px', margin: '0 auto' }} />
          <p style={{ fontWeight: '600', color: '#fff', marginBottom: '4px' }}>Belum Ada Riwayat Scan</p>
          <p style={{ fontSize: '13px' }}>Jalankan pemindaian pertama Anda di menu **Scan Target**.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}></th>
                  <th>ID</th>
                  <th>Target Directory</th>
                  <th>Waktu Scan</th>
                  <th>Sumber / Tipe</th>
                  <th>Aksi Laporan</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => {
                  const isExpanded = expandedRow === report.id;
                  const details = detailsCache[report.id];
                  const detailsLoadingState = detailsLoading[report.id];

                  return (
                    <React.Fragment key={report.id}>
                      <tr 
                        onClick={() => toggleRow(report.id)} 
                        style={{ cursor: 'pointer', transition: 'background-color 0.2s' }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <td>
                          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        </td>
                        <td style={{ fontWeight: '600', color: '#fff' }}>#{report.id}</td>
                        <td style={{ fontWeight: '500', color: '#fff' }}>{report.target}</td>
                        <td>{formatDateTime(report.timestamp)}</td>
                        <td>
                          <span style={{ 
                            fontSize: '12px', 
                            color: report.is_scheduled ? 'var(--color-warning)' : 'var(--color-info)',
                            fontWeight: '500'
                          }}>
                            {report.is_scheduled ? '⏰ Terjadwal' : '👤 Manual'}
                          </span>
                        </td>
                        <td onClick={(e) => e.stopPropagation()}>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <a 
                              href={`${API_URL}/scan/report/${report.id}`} 
                              target="_blank" 
                              rel="noreferrer" 
                              className="btn btn-secondary"
                              style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}
                              title="Download PDF"
                            >
                              <Download size={12} /> PDF
                            </a>
                            {report.html_report_available && (
                              <a 
                                href={`${API_URL}/reports/${report.id}/html`} 
                                target="_blank" 
                                rel="noreferrer" 
                                className="btn btn-primary"
                                style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}
                                title="Lihat Laporan"
                              >
                                <ExternalLink size={12} /> HTML
                              </a>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expandable row details */}
                      {isExpanded && (
                        <tr>
                          <td colSpan="6" style={{ backgroundColor: 'var(--bg-primary)', padding: '20px', borderBottom: '1px solid var(--border-color)' }}>
                            {detailsLoadingState ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                                <RefreshCw size={14} className="spinner" /> Memuat detail temuan...
                              </div>
                            ) : details ? (
                              <div>
                                <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#fff', marginBottom: '12px' }}>Ringkasan Tingkat Kerentanan</h4>
                                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                                  <div style={{ padding: '10px 16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', borderLeft: '3px solid var(--color-danger)' }}>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Critical:</span>{' '}
                                    <strong style={{ color: 'var(--color-danger)' }}>{details.severity_counts?.Critical || 0}</strong>
                                  </div>
                                  <div style={{ padding: '10px 16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', borderLeft: '3px solid var(--color-warning)' }}>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>High:</span>{' '}
                                    <strong style={{ color: 'var(--color-warning)' }}>{details.severity_counts?.High || 0}</strong>
                                  </div>
                                  <div style={{ padding: '10px 16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', borderLeft: '3px solid var(--color-info)' }}>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Medium:</span>{' '}
                                    <strong style={{ color: 'var(--color-info)' }}>{details.severity_counts?.Medium || 0}</strong>
                                  </div>
                                  <div style={{ padding: '10px 16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', borderLeft: '3px solid var(--color-success)' }}>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Low:</span>{' '}
                                    <strong style={{ color: 'var(--color-success)' }}>{details.severity_counts?.Low || 0}</strong>
                                  </div>
                                  <div style={{ padding: '10px 16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', borderLeft: '3px solid var(--color-accent)' }}>
                                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Total Celah:</span>{' '}
                                    <strong style={{ color: 'white' }}>{details.total_vulnerabilities || 0}</strong>
                                  </div>
                                </div>
                                <div style={{ marginTop: '16px', display: 'flex', gap: '12px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                                  <span><strong>Mesin Pemindai:</strong> {details.source}</span>
                                  <span>•</span>
                                  <span><strong>Laporan HTML:</strong> {details.html_report_available ? 'Tersedia di Server' : 'Tidak tersedia'}</span>
                                </div>
                              </div>
                            ) : (
                              <div style={{ color: 'var(--color-danger)' }}>Gagal memuat data dari server.</div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
