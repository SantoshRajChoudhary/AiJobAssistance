import React, { useState } from 'react';

export default function ResumeCard({ data, onSkillClick }) {
  const [expanded, setExpanded] = useState(false);
  if (!data) return null;

  const {
    name = 'Candidate',
    contact = {},
    designation = 'Software Engineer',
    skills = [],
    experience = [],
    education = [],
    projects = [],
  } = data;

  const totalExp = experience.reduce((acc, e) => {
    const match = (e.duration || e.years || '').match(/\d+/);
    return acc + (match ? parseInt(match[0]) : 0);
  }, 0);

  return (
    <div className="fade-up" style={{
      background: 'var(--surface-1)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--r-lg)',
      overflow: 'hidden',
      maxWidth: '640px',
      width: '100%',
    }}>
      {/* Top strip */}
      <div style={{
        height: '3px',
        background: 'linear-gradient(90deg, var(--accent) 0%, transparent 100%)',
      }} />

      {/* Profile row */}
      <div style={{ padding: '16px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'var(--surface-3)',
          border: '1px solid var(--border-mid)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          fontWeight: 700,
          color: 'var(--text-1)',
          flexShrink: 0,
        }}>
          {name.charAt(0)}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-1)' }}>{name}</span>
            <span className="tag tag-green" style={{ fontSize: '10px' }}>✓ Parsed</span>
          </div>
          <div style={{ color: 'var(--text-2)', fontSize: '12px', marginTop: '1px' }}>{designation}</div>
        </div>

        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', flexShrink: 0 }}>
          {totalExp > 0 && (
            <span className="tag" style={{ fontFamily: 'var(--mono)', fontSize: '11px' }}>
              {totalExp}yr exp
            </span>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              padding: '4px 8px',
              borderRadius: 'var(--r-sm)',
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-3)',
              fontSize: '11px',
              cursor: 'pointer',
              fontFamily: 'var(--font)',
              transition: 'all 0.15s',
            }}
          >
            {expanded ? 'Less' : 'More'}
          </button>
        </div>
      </div>

      {/* Contact row */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '0 18px 14px',
        fontSize: '12px',
        color: 'var(--text-3)',
      }}>
        {contact.email && <span>✉ {contact.email}</span>}
        {contact.phone && <span>✆ {contact.phone}</span>}
        {contact.location && <span>◎ {contact.location}</span>}
      </div>

      {/* Skills */}
      {skills.length > 0 && (
        <div style={{
          padding: '12px 18px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}>
          <span style={{ fontSize: '11px', color: 'var(--text-3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Skills
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
            {skills.map((skill, i) => (
              <button
                key={i}
                onClick={() => onSkillClick && onSkillClick(skill)}
                title={`Search jobs needing ${skill}`}
                className="tag"
                style={{
                  background: 'var(--surface-2)',
                  cursor: 'pointer',
                  fontFamily: 'var(--font)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--r-sm)',
                  transition: 'border-color 0.15s, color 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent-mid)'; e.currentTarget.style.color = 'var(--accent)'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)'; }}
              >
                {skill}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Expanded sections */}
      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)' }}>
          {/* Experience */}
          {experience.length > 0 && (
            <div style={{ padding: '14px 18px', borderBottom: experience.length && education.length ? '1px solid var(--border)' : 'none' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
                Experience
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {experience.map((exp, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px' }}>
                    <div style={{
                      width: '2px',
                      background: i === 0 ? 'var(--accent)' : 'var(--surface-3)',
                      borderRadius: '2px',
                      flexShrink: 0,
                      minHeight: '40px',
                    }} />
                    <div>
                      <div style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-1)' }}>{exp.role || exp.title}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-2)', marginTop: '1px' }}>
                        {exp.company}
                        {(exp.duration || exp.years) && (
                          <span style={{ color: 'var(--text-3)', marginLeft: '6px', fontFamily: 'var(--mono)', fontSize: '11px' }}>
                            {exp.duration || exp.years}
                          </span>
                        )}
                      </div>
                      {exp.description && (
                        <p style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: '4px', lineHeight: 1.6 }}>
                          {exp.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {education.length > 0 && (
            <div style={{ padding: '14px 18px', borderBottom: projects.length ? '1px solid var(--border)' : 'none' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
                Education
              </div>
              {education.map((edu, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-2)', marginBottom: i < education.length - 1 ? '6px' : 0 }}>
                  <span>{edu.degree || edu.institution}</span>
                  <span style={{ color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{edu.year || edu.duration}</span>
                </div>
              ))}
            </div>
          )}

          {/* Projects */}
          {projects.length > 0 && (
            <div style={{ padding: '14px 18px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-3)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
                Projects
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {projects.map((proj, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 500, fontSize: '13px', color: 'var(--text-1)' }}>{proj.name}</span>
                      {proj.tech_stack?.length > 0 && (
                        <span style={{ fontSize: '11px', color: 'var(--accent)', fontFamily: 'var(--mono)' }}>
                          [{Array.isArray(proj.tech_stack) ? proj.tech_stack.join(', ') : proj.tech_stack}]
                        </span>
                      )}
                    </div>
                    {proj.description && (
                      <p style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: '2px', lineHeight: 1.5 }}>
                        {proj.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
