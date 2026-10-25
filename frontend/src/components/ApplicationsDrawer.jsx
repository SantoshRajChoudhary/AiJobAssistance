import React from 'react';

export default function ApplicationsDrawer({ isOpen, onClose, applications = [] }) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.55)',
          zIndex: 40,
        }}
      />

      {/* Drawer */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '380px',
        background: 'var(--surface-0)',
        borderLeft: '1px solid var(--border)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-8px 0 40px rgba(0,0,0,0.5)',
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-1)' }}>Applications</div>
            <div style={{ fontSize: '11px', color: 'var(--text-3)', marginTop: '1px' }}>
              {applications.length} submitted
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: '28px',
              height: '28px',
              borderRadius: 'var(--r-sm)',
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              color: 'var(--text-2)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'var(--font)',
              fontSize: '14px',
            }}
          >
            ✕
          </button>
        </div>

        {/* List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          {applications.length === 0 ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'var(--text-3)',
              textAlign: 'center',
              gap: '8px',
              padding: '40px 20px',
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'var(--surface-2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                marginBottom: '4px',
              }}>
                📋
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-2)', fontWeight: 500 }}>No applications yet</div>
              <div style={{ fontSize: '12px', lineHeight: 1.6, maxWidth: '240px' }}>
                Upload your resume and click Apply on any matching role
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {applications.map((app, i) => (
                <div key={app.job_id || i} style={{
                  background: 'var(--surface-1)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-md)',
                  padding: '12px 14px',
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: '8px',
                    marginBottom: '8px',
                  }}>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-1)', marginBottom: '2px' }}>
                        {app.title}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-2)' }}>{app.company}</div>
                    </div>
                    <span className="tag tag-green" style={{ flexShrink: 0 }}>
                      {app.status || 'Applied'}
                    </span>
                  </div>

                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '11px',
                    color: 'var(--text-3)',
                    fontFamily: 'var(--mono)',
                  }}>
                    <span>{app.job_id}</span>
                    <span>
                      {app.applied_date
                        ? new Date(app.applied_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
                        : 'Today'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
