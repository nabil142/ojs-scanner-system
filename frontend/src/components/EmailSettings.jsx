import React, { useEffect, useState } from 'react';
import { Mail, Check, AlertTriangle, RefreshCw, Save } from 'lucide-react';

export default function EmailSettings({ token }) {
  const [email, setEmail] = useState('');
  const [receiveReports, setReceiveReports] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/email-settings?token=${token}`);
      const data = await res.json();
      
      if (res.ok) {
        setEmail(data.email || '');
        setReceiveReports(data.receive_reports || false);
      } else {
        throw new Error(data.detail || 'Gagal memuat pengaturan email');
      }
    } catch (err) {
      setError('Gagal menghubungkan ke server untuk membaca pengaturan email.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchSettings();
    }
  }, [token]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch(`http://127.0.0.1:8000/auth/email-settings?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: email,
          receive_reports: receiveReports
        })
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess('Pengaturan notifikasi email berhasil diperbarui!');
        // Refresh settings from server
        setEmail(data.email || '');
        setReceiveReports(data.receive_reports || false);
      } else {
        throw new Error(data.detail || 'Gagal menyimpan pengaturan email.');
      }
    } catch (err) {
      setError(err.message || 'Gagal menyimpan data ke server backend.');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '200px' }}>
        <RefreshCw className="spinner" size={32} style={{ color: 'var(--color-accent)', marginBottom: '12px' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Memuat pengaturan email...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1 className="h1">Pengaturan Notifikasi Laporan</h1>

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

      {success && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          borderRadius: 'var(--radius-sm)',
          padding: '16px',
          color: 'var(--color-success)',
          marginBottom: '24px',
          fontSize: '14px'
        }}>
          <Check size={18} />
          <span>{success}</span>
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '24px' }}>
          <div style={{ padding: '8px', backgroundColor: 'var(--color-accent-alpha)', borderRadius: '8px', color: 'var(--color-accent)' }}>
            <Mail size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>Notifikasi Email Otomatis</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Kirim berkas laporan HTML & PDF hasil scan terjadwal langsung ke inbox email Anda.</p>
          </div>
        </div>

        <form onSubmit={handleSave}>
          <div className="form-group">
            <label>Alamat Email Penerima</label>
            <input
              type="email"
              className="form-input"
              placeholder="contoh: auditor@kampus.ac.id"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={saving}
              required
            />
          </div>

          <div style={{ 
            display: 'flex', 
            alignItems: 'flex-start', 
            gap: '12px', 
            backgroundColor: 'var(--bg-primary)', 
            padding: '16px', 
            borderRadius: 'var(--radius-sm)', 
            border: '1px solid var(--border-color)',
            marginBottom: '28px' 
          }}>
            <input
              type="checkbox"
              id="receiveReports"
              style={{ marginTop: '4px', cursor: 'pointer' }}
              checked={receiveReports}
              onChange={(e) => setReceiveReports(e.target.checked)}
              disabled={saving}
            />
            <label htmlFor="receiveReports" style={{ cursor: 'pointer', userSelect: 'none' }}>
              <span style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#fff', marginBottom: '2px' }}>
                Aktifkan Pengiriman Laporan
              </span>
              <span style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                Jika dicentang, setiap kali pemindaian terjadwal di latar belakang selesai (default setiap 6 jam), sistem akan otomatis mengirimkan laporan visual terbaru ke alamat email di atas.
              </span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" style={{ padding: '12px 24px' }} disabled={saving}>
              {saving ? <RefreshCw className="spinner" size={16} /> : <Save size={16} />} Simpan Preferensi
            </button>
          </div>
        </form>
      </div>

      {/* Info Card on SMTP Setup status */}
      <div className="card" style={{ marginTop: '24px', backgroundColor: 'rgba(245, 158, 11, 0.05)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
          <AlertTriangle size={18} style={{ color: 'var(--color-warning)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>Catatan Pengiriman SMTP</h4>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              Pastikan Anda sudah mengonfigurasi variabel lingkungan email di berkas <code>.env</code> project Anda (seperti <code>SMTP_SERVER</code>, <code>SENDER_EMAIL</code>, dan <code>SENDER_PASSWORD</code>/App Password) agar server backend dapat mengirimkan email dengan sukses.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
