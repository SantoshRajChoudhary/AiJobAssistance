import React, { useState } from 'react';

export default function JobCard({ job, index, isApplied = false, onApply, isApplying = false }) {
  const [expanded, setExpanded] = useState(false);
  if (!job) return null;

  const {
    job_id = 'JOB-001',
    title = 'Software Engineer',
    company = 'Company',
    location = 'Remote',
    experience_required = 'Any',
    skills = [],
    description = '',
    source_link = '#',
    match_score = null,
    match_reason = '',
  } = job;

  const isRemote = location.toLowerCase().includes('remote');

  return (
    <div
      className="fade-up"
      style={{
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-mid)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ padding: '16px 18px' }}>
        {/* Top row: index + score */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', align: 'center', gap: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
              #{(index ?? 0) + 1}
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>
              · {job_id}
            </span>
          </div>

          {match_score && (
            <div style={{
              fontFamily: 'var(--mono)',
              fontSize: '12px',
              fontWeight: 500,
              color: match_score >= 90 ? 'var(--green)' : 'var(--accent)',
              background: match_score >= 90 ? 'var(--green-dim)' : 'var(--accent-dim)',
              padding: '2px 8px',
              borderRadius: '99px',
              border: `1px solid ${match_score >= 90 ? 'rgba(62,207,142,0.25)' : 'rgba(232,160,69,0.25)'}`,
            }}>
              {match_score}% match
            </div>
          )}
        </div>

        {/* Title + company */}
        <div style={{ marginBottom: '10px' }}>
          <h3 style={{
            fontSize: '15px',
            fontWeight: 600,
            color: 'var(--text-1)',
            letterSpacing: '-0.02em',
            lineHeight: 1.3,
            marginBottom: '4px',
          }}>
            {title}
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '12px', color: 'var(--text-2)' }}>
            <span>{company}</span>
            <span style={{ color: isRemote ? 'var(--green)' : 'var(--text-3)' }}>
              {isRemote ? '↗ ' : ''}{location}
            </span>
            <span style={{ color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{experience_required}</span>
          </div>
        </div>

        {/* Match reason */}
        {match_reason && (
          <div style={{
            padding: '10px 12px',
            background: 'var(--surface-2)',
            borderRadius: 'var(--r-md)',
            fontSize: '12px',
            color: 'var(--text-2)',
            lineHeight: 1.6,
            marginBottom: '12px',
            borderLeft: '2px solid var(--accent)',
          }}>
            {match_reason}
          </div>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginBottom: '14px' }}>
            {skills.slice(0, 7).map((s, i) => (
              <span key={i} className="tag">{s}</span>
            ))}
            {skills.length > 7 && (
              <span className="tag" style={{ color: 'var(--text-3)' }}>+{skills.length - 7}</span>
            )}
          </div>
        )}

        {/* Description toggle */}
        {description && (
          <div style={{ marginBottom: '14px' }}>
            <p style={{
              fontSize: '12px',
              color: 'var(--text-3)',
              lineHeight: 1.6,
              display: expanded ? 'block' : '-webkit-box',
              WebkitLineClamp: expanded ? 'unset' : 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {description}
            </p>
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-3)',
                fontSize: '11px',
                cursor: 'pointer',
                fontFamily: 'var(--font)',
                padding: '2px 0',
                marginTop: '4px',
                textDecoration: 'underline',
              }}
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          </div>
        )}

        {/* Actions */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: '12px',
          borderTop: '1px solid var(--border)',
        }}>
          {source_link && source_link !== '#' ? (
            <a
              href={source_link}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: '11px',
                color: 'var(--text-3)',
                textDecoration: 'none',
                fontFamily: 'var(--mono)',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--text-2)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
            >
              View listing ↗
            </a>
          ) : <span />}

          {isApplied ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              padding: '6px 14px',
              borderRadius: 'var(--r-md)',
              background: 'var(--green-dim)',
              border: '1px solid rgba(62,207,142,0.2)',
              color: 'var(--green)',
              fontSize: '12px',
              fontWeight: 500,
            }}>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              Applied
            </div>
          ) : (
            <button
              onClick={() => onApply && onApply(job, index)}
              disabled={isApplying}
              style={{
                padding: '6px 16px',
                borderRadius: 'var(--r-md)',
                background: isApplying ? 'var(--surface-3)' : 'var(--accent)',
                border: 'none',
                color: isApplying ? 'var(--text-3)' : '#000',
                fontSize: '12px',
                fontWeight: 600,
                cursor: isApplying ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font)',
                letterSpacing: '-0.01em',
                transition: 'opacity 0.15s',
              }}
              onMouseEnter={e => { if (!isApplying) e.currentTarget.style.opacity = '0.85'; }}
              onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
            >
              {isApplying ? 'Applying…' : 'Apply'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
