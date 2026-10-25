import React, { useState, useRef } from 'react';

export default function ChatInput({
  onSendMessage,
  onFileUpload,
  isLoading = false,
  uploadingFile = null,
  suggestions = [],
}) {
  const [text, setText] = useState('');
  const fileRef = useRef(null);

  const chips = suggestions.length > 0 ? suggestions : [
    'Show remote roles',
    'Jobs needing React',
    'Apply to job 1',
    'My applied jobs',
    'Entry level only',
  ];

  const handleSubmit = e => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim());
    setText('');
  };

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFile = e => {
    const file = e.target.files?.[0];
    if (file) { onFileUpload(file); e.target.value = ''; }
  };

  return (
    <div style={{
      flexShrink: 0,
      borderTop: '1px solid var(--border)',
      background: 'var(--surface-0)',
      padding: '10px 16px 12px',
    }}>
      {/* Upload progress */}
      {uploadingFile && (
        <div style={{
          marginBottom: '8px',
          padding: '8px 12px',
          background: 'var(--accent-dim)',
          border: '1px solid var(--accent-mid)',
          borderRadius: 'var(--r-md)',
          fontSize: '12px',
          color: 'var(--accent)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          <span style={{
            width: '12px', height: '12px',
            border: '1.5px solid var(--accent)',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            flexShrink: 0,
          }} />
          Parsing {uploadingFile.name}…
        </div>
      )}

      {/* Suggestion chips */}
      <div style={{
        display: 'flex',
        gap: '5px',
        overflowX: 'auto',
        marginBottom: '8px',
        scrollbarWidth: 'none',
      }}>
        {chips.map((chip, i) => (
          <button
            key={i}
            onClick={() => !isLoading && onSendMessage(chip)}
            style={{
              flexShrink: 0,
              padding: '4px 10px',
              borderRadius: '99px',
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              color: 'var(--text-3)',
              fontSize: '11px',
              fontWeight: 500,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font)',
              whiteSpace: 'nowrap',
              transition: 'border-color 0.15s, color 0.15s',
            }}
            onMouseEnter={e => { if (!isLoading) { e.currentTarget.style.borderColor = 'var(--border-mid)'; e.currentTarget.style.color = 'var(--text-2)'; }}}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-3)'; }}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input row */}
      <form onSubmit={handleSubmit} style={{
        display: 'flex',
        gap: '6px',
        alignItems: 'center',
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-md)',
        padding: '0 8px 0 4px',
        transition: 'border-color 0.15s',
      }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--border-mid)'}
        onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
      >
        <input
          type="file"
          accept=".pdf,.docx"
          ref={fileRef}
          onChange={handleFile}
          style={{ display: 'none' }}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          title="Attach resume (PDF or DOCX)"
          style={{
            padding: '8px',
            background: 'none',
            border: 'none',
            color: 'var(--text-3)',
            cursor: 'pointer',
            fontSize: '15px',
            lineHeight: 1,
            borderRadius: 'var(--r-sm)',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--text-1)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
        >
          ⌘
        </button>

        <input
          type="text"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask anything… or upload a resume to get started"
          disabled={isLoading}
          style={{
            flex: 1,
            background: 'none',
            border: 'none',
            outline: 'none',
            color: 'var(--text-1)',
            fontSize: '13px',
            fontFamily: 'var(--font)',
            padding: '10px 4px',
          }}
        />

        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          style={{
            padding: '6px 12px',
            borderRadius: 'var(--r-sm)',
            background: text.trim() && !isLoading ? 'var(--accent)' : 'var(--surface-3)',
            border: 'none',
            color: text.trim() && !isLoading ? '#000' : 'var(--text-3)',
            fontSize: '12px',
            fontWeight: 600,
            cursor: text.trim() && !isLoading ? 'pointer' : 'not-allowed',
            fontFamily: 'var(--font)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            transition: 'all 0.15s',
          }}
        >
          {isLoading ? (
            <span style={{
              width: '12px',
              height: '12px',
              border: '1.5px solid var(--text-3)',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
              display: 'inline-block',
            }} />
          ) : (
            <>Send ↵</>
          )}
        </button>
      </form>
    </div>
  );
}
