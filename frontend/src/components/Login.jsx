import React, { useState } from 'react';
import { Lock, User, AlertCircle, CheckCircle } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    if (!username || !password) {
      setError('Username dan password harus diisi');
      return;
    }

    setLoading(true);
    const endpoint = isRegister ? 'register' : 'login';
    // Gunakan query parameters sesuai dengan spesifikasi backend FastAPI
    const url = `http://127.0.0.1:8000/auth/${endpoint}?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'application/json'
        }
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Terjadi kesalahan pada server');
      }

      if (data.status === 'success' || data.token) {
        if (isRegister) {
          setSuccess('Registrasi berhasil! Silakan login.');
          setIsRegister(false);
          setPassword('');
        } else {
          localStorage.setItem('token', data.token);
          localStorage.setItem('username', username);
          onLoginSuccess(data.token, username);
        }
      } else {
        setError('Gagal memproses permintaan');
      }
    } catch (err) {
      setError(err.message || 'Koneksi ke server gagal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'radial-gradient(circle at center, #1e293b 0%, #0f172a 100%)',
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)',
        padding: '32px',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            display: 'inline-flex',
            padding: '12px',
            backgroundColor: 'var(--color-accent-alpha)',
            borderRadius: '50%',
            color: 'var(--color-accent)',
            marginBottom: '16px'
          }}>
            <Lock size={28} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#fff', marginBottom: '8px' }}>
            {isRegister ? 'Buat Akun Auditor' : 'Login Auditor SAST'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            {isRegister ? 'Daftar untuk memonitor keamanan OJS' : 'Masuk untuk mengakses dashboard scanner'}
          </p>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
            color: 'var(--color-danger)',
            fontSize: '13.5px',
            marginBottom: '20px'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
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
            padding: '12px',
            color: 'var(--color-success)',
            fontSize: '13.5px',
            marginBottom: '20px'
          }}>
            <CheckCircle size={18} style={{ flexShrink: 0 }} />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <div style={{ position: 'relative' }}>
              <User size={18} style={{
                position: 'absolute',
                left: '14px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }} />
              <input
                type="text"
                className="form-input"
                placeholder="Masukkan username"
                style={{ paddingLeft: '42px' }}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '28px' }}>
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} style={{
                position: 'absolute',
                left: '14px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }} />
              <input
                type="password"
                className="form-input"
                placeholder="Masukkan password"
                style={{ paddingLeft: '42px' }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: '15px' }}
            disabled={loading}
          >
            {loading ? (isRegister ? 'Mendaftar...' : 'Memproses...') : (isRegister ? 'Daftar Sekarang' : 'Masuk Dashboard')}
          </button>
        </form>

        <div style={{
          marginTop: '24px',
          textAlign: 'center',
          fontSize: '14px',
          color: 'var(--text-secondary)'
        }}>
          {isRegister ? 'Sudah punya akun?' : 'Belum punya akun?'}{' '}
          <button
            type="button"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-accent)',
              fontWeight: '600',
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
            onClick={() => {
              setIsRegister(!isRegister);
              setError('');
              setSuccess('');
            }}
            disabled={loading}
          >
            {isRegister ? 'Masuk' : 'Daftar Akun'}
          </button>
        </div>
      </div>
    </div>
  );
}
