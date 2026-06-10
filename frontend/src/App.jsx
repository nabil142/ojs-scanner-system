import React, { useState, useEffect } from 'react';
import { LayoutDashboard, ShieldAlert, History, Mail, LogOut, Shield } from 'lucide-react';
import Login from './components/Login';
import DashboardOverview from './components/DashboardOverview';
import ScanTarget from './components/ScanTarget';
import ScanHistory from './components/ScanHistory';
import EmailSettings from './components/EmailSettings';

export default function App() {
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    // Check if token exists in localStorage on mount
    const savedToken = localStorage.getItem('token');
    const savedUsername = localStorage.getItem('username');
    if (savedToken) {
      setToken(savedToken);
      setUsername(savedUsername || 'Auditor');
    }
  }, []);

  const handleLoginSuccess = (newToken, newUsername) => {
    setToken(newToken);
    setUsername(newUsername);
    setActiveTab('overview');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setToken(null);
    setUsername('');
  };

  // If not logged in, show Login Screen
  if (!token) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // Sidebar navigation options
  const navItems = [
    { id: 'overview', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'scan', label: 'SAST Scan', icon: <ShieldAlert size={18} /> },
    { id: 'history', label: 'Riwayat Scan', icon: <History size={18} /> },
    { id: 'settings', label: 'Settings Email', icon: <Mail size={18} /> }
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        {/* App Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '32px', padding: '0 8px' }}>
          <div style={{
            padding: '8px',
            backgroundColor: 'var(--color-accent)',
            borderRadius: '8px',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Shield size={20} />
          </div>
          <span style={{ fontWeight: '700', fontSize: '18px', color: 'white', letterSpacing: '0.5px' }}>OJS SAST Scan</span>
        </div>

        {/* User profile brief */}
        <div style={{
          backgroundColor: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px',
          marginBottom: '24px',
          fontSize: '13.5px'
        }}>
          <span style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '11px', textTransform: 'uppercase', fontWeight: '500', marginBottom: '2px' }}>Role Auditor</span>
          <strong style={{ color: 'white' }}>{username}</strong>
        </div>

        {/* Nav Links */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-sm)',
                  backgroundColor: isActive ? 'var(--color-accent)' : 'transparent',
                  color: isActive ? 'white' : 'var(--text-secondary)',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontWeight: isActive ? '600' : '500',
                  fontSize: '14.5px',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)';
                    e.currentTarget.style.color = 'white';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: 'var(--color-danger)',
            border: '1px solid rgba(239, 68, 68, 0.15)',
            textAlign: 'left',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s ease',
            marginTop: 'auto'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-danger)';
            e.currentTarget.style.color = 'white';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
            e.currentTarget.style.color = 'var(--color-danger)';
          }}
        >
          <LogOut size={16} />
          <span>Keluar (Logout)</span>
        </button>
      </aside>

      {/* Main Panel Content */}
      <main className="main-content">
        {activeTab === 'overview' && <DashboardOverview />}
        {activeTab === 'scan' && <ScanTarget />}
        {activeTab === 'history' && <ScanHistory />}
        {activeTab === 'settings' && <EmailSettings token={token} />}
      </main>
    </div>
  );
}
