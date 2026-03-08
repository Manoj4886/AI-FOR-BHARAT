import { useEffect, useRef, useState } from 'react';
import './AnimatedAvatar.css';

// Lip-shape presets: [mouthOpenY, mouthWidth, lipCurve]
const VISEME_SHAPES = {
    sil: [0, 32, 1],
    PP: [2, 28, 0],    // m/b/p  lips together
    FF: [4, 30, -0.5], // f/v    teeth on lip
    TH: [5, 31, 0],    // th
    DD: [6, 30, 0],    // d/t
    kk: [7, 29, 0.5],  // k/g
    CH: [6, 27, -0.5], // ch/sh
    SS: [4, 26, 0],    // s/z
    nn: [5, 30, 0],    // n/l
    RR: [8, 28, 0.5],  // r
    aa: [14, 34, 1],    // ah
    E: [10, 33, 1],    // eh
    I: [8, 34, 1.5],  // ee
    O: [13, 26, 1],    // oh
    U: [10, 24, 0.5],  // oo
};

function lerp(a, b, t) { return a + (b - a) * t; }

export default function AnimatedAvatar({ agentState = 'idle', isSpeaking, currentViseme }) {
    // Eye blink
    const [blink, setBlink] = useState(false);
    // Lip shape [openY, width, curve]
    const [lip, setLip] = useState([0, 32, 1]);
    // Head sway offset (deg)
    const [headSway, setHeadSway] = useState(0);
    // Hand gesture index (0–3)
    const [gesture, setGesture] = useState(0);
    // Eyebrow raise (0–1)
    const [brow, setBrow] = useState(0);
    // Thinking dots phase
    const [dotPhase, setDotPhase] = useState(0);

    const rafRef = useRef(null);
    const blinkRef = useRef(null);
    const gestureRef = useRef(null);
    const startRef = useRef(performance.now());

    // ── Eye blink scheduler ─────────────────────────────────────────────────
    useEffect(() => {
        const schedule = () => {
            blinkRef.current = setTimeout(() => {
                setBlink(true);
                setTimeout(() => setBlink(false), 130);
                schedule();
            }, 2800 + Math.random() * 2400);
        };
        schedule();
        return () => clearTimeout(blinkRef.current);
    }, []);

    // ── Mouth / lip ─────────────────────────────────────────────────────────
    useEffect(() => {
        const key = currentViseme?.replace('viseme_', '') || 'sil';
        const target = isSpeaking ? (VISEME_SHAPES[key] || VISEME_SHAPES.aa) : VISEME_SHAPES.sil;
        setLip(prev => [
            lerp(prev[0], target[0], 0.35),
            lerp(prev[1], target[1], 0.35),
            lerp(prev[2], target[2], 0.35),
        ]);
    }, [currentViseme, isSpeaking]);

    // ── Continuous animation frame (head sway, brow, dots) ─────────────────
    useEffect(() => {
        const tick = () => {
            const t = (performance.now() - startRef.current) / 1000;
            setHeadSway(Math.sin(t * 0.8) * 3.5);
            setBrow(agentState === 'thinking' ? 0.55 + Math.sin(t * 2) * 0.25
                : agentState === 'explaining' ? 0.15 + Math.abs(Math.sin(t * 3.5)) * 0.25
                    : 0);
            setDotPhase(t);
            rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(rafRef.current);
    }, [agentState]);

    // ── Hand gesture cycling while explaining ───────────────────────────────
    useEffect(() => {
        if (agentState === 'explaining') {
            gestureRef.current = setInterval(() => {
                setGesture(g => (g + 1) % 4);
            }, 1800);
        } else {
            clearInterval(gestureRef.current);
            setGesture(0);
        }
        return () => clearInterval(gestureRef.current);
    }, [agentState]);

    const [openY, mW, lipC] = lip;
    const isTalking = isSpeaking && openY > 1;
    const isListening = agentState === 'listening';
    const isThinking = agentState === 'thinking';
    const isExplaining = agentState === 'explaining';

    // Mouth SVG path
    const cx = 100, cy = 178;
    const mouthPath = isTalking
        ? `M${cx - mW / 2},${cy}
       C${cx - mW / 2 + 4},${cy + openY * 0.6} ${cx + mW / 2 - 4},${cy + openY * 0.6} ${cx + mW / 2},${cy}
       C${cx + mW / 2 - 4},${cy + openY} ${cx - mW / 2 + 4},${cy + openY} ${cx - mW / 2},${cy} Z`
        : `M${cx - mW / 2},${cy} Q${cx},${cy + lipC * 3} ${cx + mW / 2},${cy}`;

    const eyeScaleY = blink ? 0.05 : 1;

    return (
        <div className={`aa-wrap aa-${agentState}`}>
            {/* Ambient glow ring */}
            <div className="aa-ring" />

            {/* Main SVG character */}
            <svg
                viewBox="0 0 200 340"
                className="aa-svg"
                style={{ transform: `rotate(${headSway}deg)`, transformOrigin: '100px 80px' }}
                aria-label="AI Tutor Avatar"
            >
                <defs>
                    {/* Skin gradient */}
                    <radialGradient id="skinGrad" cx="50%" cy="35%" r="60%">
                        <stop offset="0%" stopColor="#f9c89b" />
                        <stop offset="100%" stopColor="#e8924a" />
                    </radialGradient>
                    {/* Shirt gradient */}
                    <linearGradient id="shirtGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#3d4fd9" />
                        <stop offset="100%" stopColor="#1e2a9a" />
                    </linearGradient>
                    {/* Collar gradient */}
                    <linearGradient id="collarGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f0f0f0" />
                        <stop offset="100%" stopColor="#d0d0d0" />
                    </linearGradient>
                    {/* Hair gradient */}
                    <radialGradient id="hairGrad" cx="50%" cy="20%" r="70%">
                        <stop offset="0%" stopColor="#3d2b1f" />
                        <stop offset="100%" stopColor="#1a0f08" />
                    </radialGradient>
                    {/* Shadow filter */}
                    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#00000040" />
                    </filter>
                    {/* Speaking glow on mouth */}
                    <filter id="mouthGlow">
                        <feGaussianBlur stdDeviation="2" result="blur" />
                        <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                    </filter>
                </defs>

                {/* ── Shirt / Body ─────────────────────────────────────── */}
                <path
                    d="M50,270 Q40,240 38,210 L162,210 Q160,240 150,270 Z"
                    fill="url(#shirtGrad)" filter="url(#shadow)"
                />
                {/* Collar left */}
                <path d="M100,207 L78,230 L92,230 Z" fill="url(#collarGrad)" />
                {/* Collar right */}
                <path d="M100,207 L122,230 L108,230 Z" fill="url(#collarGrad)" />

                {/* ── ARMS / HANDS – 4 gesture states ─────────────────── */}
                <g className={`aa-hands gesture-${gesture} ${isExplaining ? 'gesturing' : ''}`}>
                    {gesture === 0 && (
                        /* Resting – arms slightly out */
                        <>
                            <path d="M55,215 Q30,230 28,260" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="28" cy="265" rx="10" ry="12" fill="url(#skinGrad)" />
                            <path d="M145,215 Q170,230 172,260" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="172" cy="265" rx="10" ry="12" fill="url(#skinGrad)" />
                        </>
                    )}
                    {gesture === 1 && (
                        /* Point forward – right hand points */
                        <>
                            <path d="M55,215 Q32,235 30,258" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="30" cy="263" rx="10" ry="12" fill="url(#skinGrad)" />
                            {/* Right arm raised pointing */}
                            <path d="M145,215 Q165,200 175,180" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="176" cy="174" rx="10" ry="12" fill="url(#skinGrad)" transform="rotate(-30 176 174)" />
                            {/* Index finger */}
                            <line x1="180" y1="170" x2="193" y2="152" stroke="url(#skinGrad)" strokeWidth="7" strokeLinecap="round" />
                        </>
                    )}
                    {gesture === 2 && (
                        /* Open palms – both hands out wide */
                        <>
                            <path d="M55,215 Q20,220 12,235" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="10" cy="240" rx="13" ry="10" fill="url(#skinGrad)" transform="rotate(-15 10 240)" />
                            <path d="M145,215 Q180,220 188,235" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="190" cy="240" rx="13" ry="10" fill="url(#skinGrad)" transform="rotate(15 190 240)" />
                        </>
                    )}
                    {gesture === 3 && (
                        /* Left hand raised, making a counting gesture */
                        <>
                            <path d="M55,215 Q35,200 28,178" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="27" cy="173" rx="10" ry="12" fill="url(#skinGrad)" transform="rotate(20 27 173)" />
                            {/* Two fingers up */}
                            <line x1="22" y1="168" x2="18" y2="150" stroke="url(#skinGrad)" strokeWidth="7" strokeLinecap="round" />
                            <line x1="30" y1="166" x2="28" y2="147" stroke="url(#skinGrad)" strokeWidth="7" strokeLinecap="round" />

                            <path d="M145,215 Q168,228 170,255" stroke="#e8924a" strokeWidth="18" strokeLinecap="round" fill="none" />
                            <ellipse cx="170" cy="260" rx="10" ry="12" fill="url(#skinGrad)" />
                        </>
                    )}
                </g>

                {/* ── Neck ─────────────────────────────────────────────── */}
                <rect x="88" y="197" width="24" height="16" rx="4" fill="#e8924a" />

                {/* ── Head ─────────────────────────────────────────────── */}
                <ellipse cx="100" cy="128" rx="55" ry="60" fill="url(#skinGrad)" filter="url(#shadow)" />

                {/* ── Hair ─────────────────────────────────────────────── */}
                <path
                    d="M46,118 Q44,66 100,58 Q156,66 154,118
             Q145,70 100,65 Q55,70 46,118 Z"
                    fill="url(#hairGrad)"
                />
                {/* Hair strand detail */}
                <path d="M100,65 Q97,58 96,52" stroke="#1a0f08" strokeWidth="3" strokeLinecap="round" fill="none" />
                <path d="M108,66 Q107,59 107,53" stroke="#1a0f08" strokeWidth="3" strokeLinecap="round" fill="none" />

                {/* ── Beard / Stubble ───────────────────────────────────── */}
                <ellipse cx="100" cy="172" rx="28" ry="16" fill="#3d2b1f" opacity="0.22" />
                <path d="M73,165 Q100,178 127,165 Q120,185 100,188 Q80,185 73,165 Z"
                    fill="#3d2b1f" opacity="0.18" />

                {/* ── Eyebrows ──────────────────────────────────────────── */}
                <g transform={`translate(0, ${-brow * 5})`}>
                    <path d="M68,106 Q80,102 90,106" stroke="#2a1a0e" strokeWidth="3.5" strokeLinecap="round" fill="none" />
                    <path d="M110,106 Q120,102 132,106" stroke="#2a1a0e" strokeWidth="3.5" strokeLinecap="round" fill="none" />
                </g>

                {/* ── Eyes ─────────────────────────────────────────────── */}
                {/* Left eye white */}
                <ellipse cx="79" cy="120" rx="12" ry="10" fill="white" />
                {/* Left iris */}
                <ellipse cx="79" cy="120" rx="7" ry={7 * eyeScaleY} fill="#5c3d1a" />
                {/* Left pupil */}
                <ellipse cx="79" cy="120" rx="4" ry={4 * eyeScaleY} fill="#1a0f00" />
                {/* Left eye shine */}
                <ellipse cx="81" cy="117" rx="2" ry={1.5 * eyeScaleY} fill="white" opacity="0.9" />
                {/* Left eyelid (blink) */}
                <ellipse cx="79" cy="120" rx="12" ry={blink ? 10 : 0}
                    fill="#e8924a" style={{ transition: 'ry 0.07s' }} />

                {/* Right eye white */}
                <ellipse cx="121" cy="120" rx="12" ry="10" fill="white" />
                {/* Right iris */}
                <ellipse cx="121" cy="120" rx="7" ry={7 * eyeScaleY} fill="#5c3d1a" />
                {/* Right pupil */}
                <ellipse cx="121" cy="120" rx="4" ry={4 * eyeScaleY} fill="#1a0f00" />
                {/* Right eye shine */}
                <ellipse cx="123" cy="117" rx="2" ry={1.5 * eyeScaleY} fill="white" opacity="0.9" />
                {/* Right eyelid (blink) */}
                <ellipse cx="121" cy="120" rx="12" ry={blink ? 10 : 0}
                    fill="#e8924a" style={{ transition: 'ry 0.07s' }} />

                {/* ── Nose ─────────────────────────────────────────────── */}
                <path d="M96,138 Q100,148 104,138" stroke="#c07040" strokeWidth="2" fill="none" strokeLinecap="round" />
                <circle cx="95" cy="148" r="3.5" fill="#c07040" opacity="0.5" />
                <circle cx="105" cy="148" r="3.5" fill="#c07040" opacity="0.5" />

                {/* ── Ears ─────────────────────────────────────────────── */}
                <ellipse cx="46" cy="128" rx="9" ry="13" fill="#e08050" />
                <ellipse cx="46" cy="128" rx="5" ry="9" fill="#d07040" opacity="0.5" />
                <ellipse cx="154" cy="128" rx="9" ry="13" fill="#e08050" />
                <ellipse cx="154" cy="128" rx="5" ry="9" fill="#d07040" opacity="0.5" />

                {/* ── Cheek blush ───────────────────────────────────────── */}
                <ellipse cx="70" cy="140" rx="12" ry="7" fill="#f08060" opacity="0.18" />
                <ellipse cx="130" cy="140" rx="12" ry="7" fill="#f08060" opacity="0.18" />

                {/* ── Mouth / Lip sync ─────────────────────────────────── */}
                <g filter={isTalking ? 'url(#mouthGlow)' : undefined}>
                    {isTalking ? (
                        <>
                            {/* Teeth */}
                            <ellipse cx={cx} cy={cy + openY * 0.45} rx={mW * 0.38} ry={openY * 0.32} fill="white" opacity="0.92" />
                            {/* Outer lips */}
                            <path d={mouthPath} fill="#c04030" stroke="#8b2020" strokeWidth="1.5" />
                            {/* Inner mouth */}
                            <ellipse cx={cx} cy={cy + openY * 0.6} rx={mW * 0.42} ry={openY * 0.38} fill="#3a0808" opacity="0.85" />
                            {/* Upper lip line */}
                            <path d={`M${cx - mW / 2},${cy} Q${cx - 6},${cy - 4} ${cx},${cy - 5} Q${cx + 6},${cy - 4} ${cx + mW / 2},${cy}`}
                                stroke="#8b2020" strokeWidth="2" fill="none" />
                        </>
                    ) : (
                        <path d={mouthPath} stroke="#a03530" strokeWidth="2.5" fill="none" strokeLinecap="round" />
                    )}
                </g>

                {/* ── Listening: sound waves on ears ───────────────────── */}
                {isListening && (
                    <g className="aa-ear-waves">
                        <path d="M32,122 Q25,128 32,134" stroke="#10b981" strokeWidth="2.5" fill="none" strokeLinecap="round" className="ew1" />
                        <path d="M27,116 Q16,128 27,140" stroke="#10b981" strokeWidth="2" fill="none" strokeLinecap="round" className="ew2" />
                        <path d="M168,122 Q175,128 168,134" stroke="#10b981" strokeWidth="2.5" fill="none" strokeLinecap="round" className="ew1" />
                        <path d="M173,116 Q184,128 173,140" stroke="#10b981" strokeWidth="2" fill="none" strokeLinecap="round" className="ew2" />
                    </g>
                )}

                {/* ── Thinking: dots above head ────────────────────────── */}
                {isThinking && (
                    <g className="aa-think-dots">
                        {[0, 1, 2].map(i => (
                            <circle
                                key={i}
                                cx={84 + i * 16}
                                cy={55 + Math.sin(dotPhase * 3 + i * 1.1) * 6}
                                r="5"
                                fill="#f59e0b"
                                opacity={0.6 + Math.sin(dotPhase * 3 + i * 1.1) * 0.4}
                            />
                        ))}
                    </g>
                )}
            </svg>

            {/* ── Waveform bars while speaking ──────────────────────── */}
            {isSpeaking && (
                <div className="aa-waveform">
                    {Array.from({ length: 14 }).map((_, i) => (
                        <span key={i} className="aa-bar" style={{ animationDelay: `${i * 0.07}s` }} />
                    ))}
                </div>
            )}

            {/* ── Status badge ─────────────────────────────────────── */}
            <div className={`aa-badge aa-badge-${agentState}`}>
                <span className="aa-dot" />
                {agentState === 'idle' && '👨‍🏫 AI Tutor'}
                {agentState === 'listening' && '🎙 Listening…'}
                {agentState === 'thinking' && '💭 Thinking…'}
                {agentState === 'explaining' && '🗣 Explaining'}
            </div>
        </div>
    );
}
