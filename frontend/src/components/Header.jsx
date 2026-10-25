import React from 'react';

export default function Header({ applicationCount, onOpenDrawer, onTriggerUpload }) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      height: '52px',
      background: 'var(--surface-0)',
      borderBottom: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      {/* Left: brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '26px',
          height: '26px',
          borderRadius: '6px',
          background: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {/* Simple H logo mark */}
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 2v10M12 2v10M2 7h10" stroke="#000" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-1)', letterSpacing: '-0.02em' }}>
          Hidani Jobs
        </span>
        <span style={{
          fontSize: '11px',
          color: 'var(--text-3)',
          fontFamily: 'var(--mono)',
          paddingLeft: '6px',
          borderLeft: '1px solid var(--border)',
        }}>
          AI Assistant
        </span>
      </div>

      {/* Right: status + actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '5px',
          padding: '4px 10px',
          borderRadius: '99px',
          background: 'var(--green-dim)',
          border: '1px solid rgba(62,207,142,0.2)',
        }}>
          <span style={{
            width: '5px',
            height: '5px',
            borderRadius: '50%',
            background: 'var(--green)',
            animation: 'blink 2.5s ease-in-out infinite',
          }} />
          <span style={{ fontSize: '11px', color: 'var(--green)', fontWeight: 500 }}>Online</span>
        </div>

        <button
          onClick={onTriggerUpload}
          style={{
            padding: '5px 12px',
            borderRadius: 'var(--r-md)',
            background: 'var(--surface-2)',
            border: '1px solid var(--border-mid)',
            color: 'var(--text-2)',
            fontSize: '12px',
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'var(--font)',
            transition: 'border-color 0.15s, color 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.color = 'var(--text-1)'; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)'; }}
        >
          Upload resume
        </button>

        <button
          onClick={onOpenDrawer}
          style={{
            padding: '5px 12px',
            borderRadius: 'var(--r-md)',
            background: applicationCount > 0 ? 'var(--accent-dim)' : 'var(--surface-2)',
            border: applicationCount > 0 ? '1px solid var(--accent-mid)' : '1px solid var(--border)',
            color: applicationCount > 0 ? 'var(--accent)' : 'var(--text-2)',
            fontSize: '12px',
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'var(--font)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.15s',
          }}
        >
          Applications
          {applicationCount > 0 && (
            <span style={{
              background: 'var(--accent)',
              color: '#000',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '10px',
              fontWeight: 700,
            }}>
              {applicationCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
