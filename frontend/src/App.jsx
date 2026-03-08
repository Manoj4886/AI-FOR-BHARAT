import { useCallback, useEffect, useRef, useState } from 'react';
import Avatar from './components/Avatar';
import GlassBoard from './components/GlassBoard';
import QuestionBar from './components/QuestionBar';
import Quiz from './components/Quiz';
import ProgressDashboard from './components/ProgressDashboard';
import TeacherPage from './components/TeacherPage';
import AuthPage from './components/AuthPage';
import { askQuestion } from './services/api';
import { wordToViseme } from './components/AvatarModel';
import './index.css';

// ── Decode base64 MP3 and play via Web Audio API ────────────────────────────
async function decodeAndPlay(base64, onEnded) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

  const ctx = new AudioContext();
  const buffer = await ctx.decodeAudioData(bytes.buffer);
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  source.connect(ctx.destination);
  source.start(0);
  source.onended = () => { ctx.close(); onEnded?.(); };
  return source;
}

export default function App() {
  // ── Auth state ───────────────────────────────────────────────────────────
  const [user, setUser] = useState(null); // null = not logged in
  const [authChecked, setAuthChecked] = useState(false);

  // Check localStorage for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('saarathi_token');
    const savedUser = localStorage.getItem('saarathi_user');
    if (token && savedUser) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser({ ...parsed, token });
      } catch {
        localStorage.removeItem('saarathi_token');
        localStorage.removeItem('saarathi_user');
      }
    }
    setAuthChecked(true);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('saarathi_token');
    localStorage.removeItem('saarathi_user');
    setUser(null);
  };

  // ── Main app state ──────────────────────────────────────────────────────
  const [tab, setTab] = useState('teacher');
  const [skillLevel, setSkillLevel] = useState('beginner');
  const [explanation, setExplanation] = useState('');
  const [topic, setTopic] = useState('');
  const [visualScene, setVisualScene] = useState('');
  const [flowDiagram, setFlowDiagram] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentViseme, setCurrentViseme] = useState('viseme_sil');
  const [showQuiz, setShowQuiz] = useState(false);
  const [particles, setParticles] = useState([]);
  const [isListening, setIsListening] = useState(false);

  const audioSourceRef = useRef(null);
  const visemeTimers = useRef([]);

  const agentState = isListening ? 'listening'
    : isLoading ? 'thinking'
      : isSpeaking ? 'explaining'
        : 'idle';

  useEffect(() => {
    setParticles(Array.from({ length: 18 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: 4 + Math.random() * 8,
      dur: 8 + Math.random() * 12,
      delay: Math.random() * 6,
    })));
  }, []);

  const clearVisemeTimers = () => {
    visemeTimers.current.forEach(clearTimeout);
    visemeTimers.current = [];
  };

  const scheduleVisemes = useCallback((speechMarks) => {
    clearVisemeTimers();
    const marks = speechMarks.filter(m => m.type === 'viseme');
    marks.forEach(mark => {
      const t = setTimeout(() => {
        setCurrentViseme(mark.viseme_key || 'viseme_aa');
        const silTimer = setTimeout(() => setCurrentViseme('viseme_sil'), 80);
        visemeTimers.current.push(silTimer);
      }, mark.time_ms);
      visemeTimers.current.push(t);
    });
    const lastTime = marks.length ? marks[marks.length - 1].time_ms + 200 : 0;
    const endTimer = setTimeout(() => {
      setCurrentViseme('viseme_sil');
      setIsSpeaking(false);
    }, lastTime);
    visemeTimers.current.push(endTimer);
  }, []);

  const speakPolly = useCallback(async (audio_base64, speech_marks) => {
    if (!audio_base64) return false;
    try {
      setIsSpeaking(true);
      setCurrentViseme('viseme_sil');
      scheduleVisemes(speech_marks || []);
      audioSourceRef.current = await decodeAndPlay(audio_base64, () => {
        setIsSpeaking(false);
        setCurrentViseme('viseme_sil');
        clearVisemeTimers();
      });
      return true;
    } catch {
      return false;
    }
  }, [scheduleVisemes]);

  const speakFallback = useCallback((text) => {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.pitch = 1.05;
    utter.volume = 1;
    const voices = window.speechSynthesis.getVoices();
    const pick = voices.find(v => v.name.includes('Google UK English Male'))
      || voices.find(v => v.lang.startsWith('en'))
      || voices[0];
    if (pick) utter.voice = pick;

    setIsSpeaking(true);
    setCurrentViseme('viseme_sil');

    utter.onboundary = (e) => {
      if (e.name === 'word') {
        const word = text.substr(e.charIndex, e.charLength || 4);
        const v = wordToViseme(word);
        setCurrentViseme(v);
        setTimeout(() => setCurrentViseme('viseme_sil'), Math.max(120, (e.charLength || 4) * 55));
      }
    };
    utter.onend = () => { setIsSpeaking(false); setCurrentViseme('viseme_sil'); };
    utter.onerror = () => { setIsSpeaking(false); setCurrentViseme('viseme_sil'); };
    window.speechSynthesis.speak(utter);
  }, []);

  const USER_ID = user?.email || 'anonymous_' + Math.random().toString(36).slice(2, 9);

  const handleAsk = async (question) => {
    setIsLoading(true);
    setExplanation('');
    setTopic('');
    setVisualScene('');
    setFlowDiagram('');
    stopSpeaking();

    try {
      const data = await askQuestion(question, skillLevel, USER_ID);
      setExplanation(data.explanation || '');
      setTopic(data.topic || '');
      setVisualScene(data.visual_scene || '');
      setFlowDiagram(data.flow_diagram || '');

      const ttsText = data.spoken_text || data.explanation || '';

      if (data.audio_base64) {
        await speakPolly(data.audio_base64, data.speech_marks);
      } else {
        speakFallback(ttsText);
      }
    } catch {
      setExplanation('Oops! Could not connect to the AI teacher. Make sure the backend is running.');
      speakFallback('Sorry, I could not connect to the backend right now.');
    }
    setIsLoading(false);
  };

  const stopSpeaking = () => {
    try { audioSourceRef.current?.stop(); } catch { }
    window.speechSynthesis?.cancel();
    clearVisemeTimers();
    setIsSpeaking(false);
    setCurrentViseme('viseme_sil');
  };

  const layoutClass = `layout-${skillLevel}`;

  // ── Show loading until auth check completes ─────────────────────────────
  if (!authChecked) {
    return (
      <div className="app" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ color: '#8b5cf6', fontSize: '1.2rem' }}>Loading...</div>
      </div>
    );
  }

  // ── Show AuthPage if not logged in ──────────────────────────────────────
  if (!user) {
    return <AuthPage onLogin={handleLogin} />;
  }

  // ── Main App (after login) ──────────────────────────────────────────────
  return (
    <div className="app">
      {/* Background particles */}
      <div className="particles">
        {particles.map(p => (
          <div
            key={p.id}
            className="particle"
            style={{
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: p.size,
              height: p.size,
              animationDuration: `${p.dur}s`,
              animationDelay: `${p.delay}s`,
            }}
          />
        ))}
      </div>

      {/* Cinematic ambient gradient */}
      <div className="ambient-bg" />

      {/* Header */}
      <header className="app-header">
        <div className="header-logo">
          <div className="logo-emblem">
            <span className="logo-icon-inner">⬡</span>
          </div>
          <span className="logo-text">Saar<span className="logo-accent">athi</span></span>
          <span className="logo-version">PRO</span>
        </div>
        <nav className="header-nav">
          <button
            className={`nav-btn ${tab === 'teacher' ? 'active' : ''}`}
            onClick={() => setTab('teacher')}
          >
            🎓 Teacher
          </button>
          <button
            className={`nav-btn ${tab === 'progress' ? 'active' : ''}`}
            onClick={() => setTab('progress')}
          >
            ◈ Progress
          </button>

          {/* User menu */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginLeft: '12px',
            paddingLeft: '12px',
            borderLeft: '1px solid rgba(139,92,246,0.2)',
          }}>
            <span style={{
              color: '#c4b5fd',
              fontSize: '0.8rem',
              fontWeight: 500,
            }}>
              👤 {user.name}
            </span>
            <button
              onClick={handleLogout}
              style={{
                padding: '5px 14px',
                borderRadius: '8px',
                border: '1px solid rgba(220,38,38,0.3)',
                background: 'rgba(220,38,38,0.15)',
                color: '#fca5a5',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              Logout
            </button>
          </div>
        </nav>
      </header>

      <main className="app-main">
        {tab === 'teacher' ? (
          <TeacherPage />
        ) : (
          <div className="progress-section">
            <h2 className="section-title">◈ Your Learning Progress</h2>
            <ProgressDashboard userId={USER_ID} />
          </div>
        )}
      </main>


    </div>
  );
}
