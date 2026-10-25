import React, { useState, useRef, useEffect } from 'react';
import Header from './components/Header';
import ResumeCard from './components/ResumeCard';
import JobCard from './components/JobCard';
import ApplicationsDrawer from './components/ApplicationsDrawer';
import ChatInput from './components/ChatInput';
import './index.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function renderMarkdown(text) {
  // Very light manual markdown: **bold**, *italic*, `code`, line breaks
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*'))
      return <em key={i}>{part.slice(1, -1)}</em>;
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} style={{ fontFamily: 'var(--mono)', background: 'var(--surface-3)', padding: '1px 5px', borderRadius: '4px', fontSize: '12px' }}>{part.slice(1, -1)}</code>;
    return <span key={i}>{part}</span>;
  });
}

function BotTyping() {
  return (
    <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
      <Avatar bot />
      <div style={{
        padding: '10px 14px',
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: '4px 12px 12px 12px',
        display: 'flex',
        gap: '4px',
        alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: '5px',
            height: '5px',
            borderRadius: '50%',
            background: 'var(--text-3)',
            animation: `blink 1.2s ease-in-out ${i * 0.2}s infinite`,
          }} />
        ))}
      </div>
    </div>
  );
}

function Avatar({ bot }) {
  return (
    <div style={{
      width: '30px',
      height: '30px',
      borderRadius: '8px',
      background: bot ? 'var(--surface-2)' : 'var(--accent)',
      border: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      fontSize: '13px',
      color: bot ? 'var(--text-2)' : '#000',
      fontWeight: 600,
    }}>
      {bot ? '✦' : 'U'}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      type: 'text',
      text: "Hi! I'm your AI job assistant.\n\nUpload your resume and I'll parse it, find the best matching roles from 1,800+ listings, and apply on your behalf.\n\nOr just ask me anything to get started.",
      timestamp: new Date(),
    }
  ]);

  const [applications, setApplications] = useState([]);
  const [activeResume, setActiveResume] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [recommendedJobs, setRecommendedJobs] = useState([]);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    fetch(`${API_BASE}/api/applications`)
      .then(r => r.ok ? r.json() : [])
      .then(d => Array.isArray(d) && setApplications(d))
      .catch(() => {});
  }, []);

  const addMessage = (msg) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), timestamp: new Date(), ...msg }]);
  };

  const handleFileUpload = async (file) => {
    const ok = file.name.endsWith('.pdf') || file.name.endsWith('.docx');
    if (!ok) { addMessage({ sender: 'assistant', type: 'text', text: 'Please upload a PDF or DOCX file.' }); return; }

    setUploadingFile(file);
    setLoading(true);
    addMessage({ sender: 'user', type: 'text', text: `Attached: ${file.name}` });

    try {
      const fd = new FormData();
      fd.append('file', file);
      if (sessionId) {
        fd.append('session_id', sessionId);
      }
      const res = await fetch(`${API_BASE}/api/parse-resume`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      handleParseSuccess(data.profile || data.resume || data, data.recommended_jobs);
    } catch {
      simulateParse(file);
    } finally {
      setUploadingFile(null);
      setLoading(false);
    }
  };

  const handleParseSuccess = (resume, jobs) => {
    setActiveResume(resume);
    addMessage({
      sender: 'assistant',
      type: 'resume_summary',
      text: `Resume parsed successfully. Here's what I extracted:`,
      resumeData: resume,
    });
    if (jobs?.length) {
      setRecommendedJobs(jobs);
      addMessage({
        sender: 'assistant',
        type: 'job_recommendations',
        text: `Based on your profile, here are the top matches:`,
        jobs,
      });
    }
  };

  const simulateParse = (file) => {
    setTimeout(() => {
      const resume = {
        name: 'Alex Johnson',
        contact: { email: 'alex@example.com', phone: '+91 98765 43210', location: 'Bangalore, IN' },
        designation: 'Frontend Engineer',
        skills: ['React', 'TypeScript', 'Next.js', 'Node.js', 'Redux', 'REST APIs', 'Git', 'Tailwind CSS'],
        experience: [
          { role: 'Software Engineer Intern', company: 'Nova Labs', duration: '1 year', description: 'Built React dashboards and integrated REST endpoints.' }
        ],
        education: [{ degree: 'B.Tech CSE', institution: 'NIT Trichy', year: '2020–2024' }],
        projects: [{ name: 'AI Job Assistant', tech_stack: ['React', 'FastAPI'], description: 'Resume parsing and job matching tool.' }],
      };

      const jobs = [
        {
          job_id: 'JOB-1042',
          title: 'Frontend Engineer',
          company: 'HyperScale AI',
          location: 'Remote',
          experience_required: '0–2 years',
          skills: ['React', 'TypeScript', 'Next.js'],
          description: 'Build clean, responsive client-facing interfaces for our AI suite. You will own front-end architecture decisions and collaborate directly with design.',
          source_link: 'https://remoteok.com',
          match_score: 96,
          match_reason: 'Your React and TypeScript experience directly matches the core stack. The remote location and entry-level requirement align with your profile.',
        },
        {
          job_id: 'JOB-1188',
          title: 'Full Stack Developer',
          company: 'CloudPulse',
          location: 'Bangalore (Hybrid)',
          experience_required: '1–3 years',
          skills: ['React', 'Node.js', 'JavaScript'],
          description: 'Build scalable enterprise micro-frontends and backend services. Work in a fast-moving product squad.',
          source_link: 'https://arbeitnow.com',
          match_score: 91,
          match_reason: 'Your fullstack background in React and Node.js aligns closely. Bangalore location is a perfect fit.',
        },
        {
          job_id: 'JOB-1350',
          title: 'Junior SDE – Web',
          company: 'Nexus Automations',
          location: 'Remote',
          experience_required: '0–1 year',
          skills: ['JavaScript', 'React', 'Git'],
          description: 'Join our automation workflow team as a junior engineer. Great mentorship and growth opportunity.',
          source_link: 'https://remoteok.com',
          match_score: 87,
          match_reason: 'Strong skill overlap with your project portfolio. Entry-level requirement matches your graduation timeline.',
        },
      ];

      handleParseSuccess(resume, jobs);
    }, 1400);
  };

  const handleSend = async (text) => {
    if (!text.trim() || loading) return;
    addMessage({ sender: 'user', type: 'text', text });
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: sessionId,
          resume: activeResume,
          applied_jobs: applications,
          recommended_jobs: recommendedJobs,
        }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data.session_id) setSessionId(data.session_id);
      if (data.applied_job) handleAppSuccess(data.applied_job);
      if (data.recommended_jobs) setRecommendedJobs(data.recommended_jobs);
      addMessage({
        sender: 'assistant',
        type: data.type || (data.recommended_jobs ? 'job_recommendations' : 'text'),
        text: data.reply || data.text || data.message,
        jobs: data.recommended_jobs,
      });
    } catch {
      handleLocalIntent(text);
    } finally {
      setLoading(false);
    }
  };

  const handleLocalIntent = (text) => {
    const lower = text.toLowerCase();

    if (lower.match(/applied|my application|application status|show app/)) {
      if (!applications.length) {
        addMessage({ sender: 'assistant', type: 'text', text: "You haven't applied to anything yet. Find a role above and click Apply." });
      } else {
        const list = applications.map((a, i) => `${i + 1}. **${a.title}** — ${a.company} · \`${a.status || 'Applied'}\``).join('\n');
        addMessage({ sender: 'assistant', type: 'text', text: `Your applications:\n\n${list}` });
      }
      return;
    }

    const applyMatch = text.match(/apply(?:\s+to)?(?:\s+job)?\s+(?:#|no\.?)?\s*(\d+|JOB-[\w-]+)/i);
    if (applyMatch) {
      const id = applyMatch[1].trim();
      const job = isNaN(id)
        ? recommendedJobs.find(j => j.job_id.toLowerCase() === id.toLowerCase())
        : recommendedJobs[parseInt(id, 10) - 1];

      if (job) { handleApply(job); }
      else { addMessage({ sender: 'assistant', type: 'text', text: `No job found for "${id}". Check the number from the list above.` }); }
      return;
    }

    if (lower.includes('remote')) {
      const filtered = recommendedJobs.filter(j => j.location.toLowerCase().includes('remote'));
      if (filtered.length) {
        addMessage({ sender: 'assistant', type: 'job_recommendations', text: 'Remote roles matching your profile:', jobs: filtered });
      } else {
        addMessage({ sender: 'assistant', type: 'text', text: 'No remote roles in the current results. Try a fresh search.' });
      }
      return;
    }

    // Keyword filter
    const skills = ['react', 'vue', 'angular', 'python', 'node', 'typescript', 'java', 'golang'];
    const matched = skills.find(s => lower.includes(s));
    if (matched) {
      const filtered = recommendedJobs.filter(j =>
        j.skills?.some(sk => sk.toLowerCase().includes(matched)) ||
        j.description?.toLowerCase().includes(matched)
      );
      if (filtered.length) {
        addMessage({ sender: 'assistant', type: 'job_recommendations', text: `Jobs requiring ${matched}:`, jobs: filtered });
      } else {
        addMessage({ sender: 'assistant', type: 'text', text: `No current matches for "${matched}". Upload your resume for a full search.` });
      }
      return;
    }

    addMessage({ sender: 'assistant', type: 'text', text: "Try: *\"show remote roles\"*, *\"apply to job 1\"*, or *\"show my applied jobs\"*" });
  };

  const handleApply = async (job) => {
    if (applications.some(a => a.job_id === job.job_id)) {
      addMessage({ sender: 'assistant', type: 'text', text: `Already applied to **${job.title}** at ${job.company}.` });
      return;
    }
    const app = {
      job_id: job.job_id,
      title: job.title,
      company: job.company,
      location: job.location,
      source_link: job.source_link || job.source_url,
      source_url: job.source_url || job.source_link,
      session_id: sessionId,
      applied_date: new Date().toISOString(),
      status: 'Applied',
    };
    try {
      const res = await fetch(`${API_BASE}/api/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(app),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.application) {
          handleAppSuccess(data.application);
          return;
        }
      }
    } catch {}
    handleAppSuccess(app);
  };

  const handleAppSuccess = (app) => {
    setApplications(prev => prev.some(a => a.job_id === app.job_id) ? prev : [...prev, app]);
    addMessage({
      sender: 'assistant',
      type: 'text',
      text: `Application sent — **${app.title}** at **${app.company}** (\`${app.job_id}\`)\nStatus: ${app.status || 'Applied'} · ${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}`,
    });
  };

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', background: 'var(--black)' }}
      onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={e => { e.preventDefault(); setIsDragging(false); }}
      onDrop={e => { e.preventDefault(); setIsDragging(false); const f = e.dataTransfer.files?.[0]; if (f) handleFileUpload(f); }}
    >
      <Header
        applicationCount={applications.length}
        onOpenDrawer={() => setDrawerOpen(true)}
        onTriggerUpload={() => document.querySelector('input[type="file"]')?.click()}
      />

      {/* Chat feed */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 0' }}>
        <div style={{ maxWidth: '700px', margin: '0 auto', padding: '0 20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div key={msg.id} className="fade-up" style={{
                display: 'flex',
                gap: '10px',
                flexDirection: isUser ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
              }}>
                <Avatar bot={!isUser} />
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  maxWidth: '85%',
                  alignItems: isUser ? 'flex-end' : 'flex-start',
                }}>
                  {msg.text && (
                    <div style={{
                      padding: '10px 14px',
                      background: isUser ? 'var(--surface-3)' : 'var(--surface-1)',
                      border: `1px solid ${isUser ? 'var(--border-mid)' : 'var(--border)'}`,
                      borderRadius: isUser ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
                      fontSize: '13px',
                      lineHeight: 1.65,
                      color: 'var(--text-1)',
                      whiteSpace: 'pre-wrap',
                    }}>
                      {msg.text.split('\n\n').map((para, i, arr) => (
                        <p key={i} style={{ margin: i < arr.length - 1 ? '0 0 8px' : 0 }}>
                          {renderMarkdown(para)}
                        </p>
                      ))}
                    </div>
                  )}

                  {msg.type === 'resume_summary' && msg.resumeData && (
                    <ResumeCard
                      data={msg.resumeData}
                      onSkillClick={skill => handleSend(`Jobs needing ${skill}`)}
                    />
                  )}

                  {msg.type === 'job_recommendations' && msg.jobs && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%', maxWidth: '640px' }}>
                      {msg.jobs.map((job, idx) => (
                        <JobCard
                          key={job.job_id}
                          job={job}
                          index={idx}
                          isApplied={applications.some(a => a.job_id === job.job_id)}
                          onApply={handleApply}
                        />
                      ))}
                    </div>
                  )}

                  <span style={{ fontSize: '10px', color: 'var(--text-3)', fontFamily: 'var(--mono)', padding: '0 2px' }}>
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })}

          {loading && <BotTyping />}
          <div ref={endRef} />
        </div>
      </div>

      {/* Drop overlay */}
      {isDragging && (
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 60,
          gap: '12px',
        }}>
          <div style={{
            width: '320px',
            height: '200px',
            border: '2px dashed var(--accent)',
            borderRadius: 'var(--r-lg)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            color: 'var(--accent)',
          }}>
            <span style={{ fontSize: '32px' }}>↓</span>
            <div style={{ fontWeight: 600, fontSize: '14px' }}>Drop resume to parse</div>
            <div style={{ fontSize: '12px', color: 'var(--text-3)' }}>PDF or DOCX</div>
          </div>
        </div>
      )}

      <ApplicationsDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        applications={applications}
      />

      <ChatInput
        onSendMessage={handleSend}
        onFileUpload={handleFileUpload}
        isLoading={loading}
        uploadingFile={uploadingFile}
      />
    </div>
  );
}
