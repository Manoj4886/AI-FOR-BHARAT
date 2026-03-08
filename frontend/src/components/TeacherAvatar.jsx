import { useEffect, useState, useRef } from 'react';
import teacherImg from '../assets/teacher.png';
import './TeacherAvatar.css';

// ─────────────────────────────────────────────────────────────────
//  CONTENT-REACTIVE ANIMATION ENGINE
//  Analyzes text content (from AI responses or typed commands)
//  and automatically maps keywords → animation state
// ─────────────────────────────────────────────────────────────────

const ANIMATION_STATES = {
    idle: { label: '👨‍🏫 Standing by', color: '#6366f1', dot: '#6366f1' },
    raiseRightHand: { label: '🙋 Right hand raised', color: '#f59e0b', dot: '#f59e0b' },
    raiseLeftHand: { label: '🙋 Left hand raised', color: '#f59e0b', dot: '#f59e0b' },
    lowerRightHand: { label: '⬇ Right hand lowered', color: '#64748b', dot: '#64748b' },
    lowerLeftHand: { label: '⬇ Left hand lowered', color: '#64748b', dot: '#64748b' },
    waveRight: { label: '👋 Waving', color: '#fbbf24', dot: '#fbbf24' },
    foldHands: { label: '🤝 Hands folded', color: '#8b5cf6', dot: '#8b5cf6' },
    pointBoard: { label: '👉 Pointing at board', color: '#f59e0b', dot: '#f59e0b' },
    writeBoard: { label: '✍️ Writing on board', color: '#34d399', dot: '#34d399' },
    underline: { label: '〰️ Underlining', color: '#f87171', dot: '#f87171' },
    highlight: { label: '🟡 Highlighting', color: '#fbbf24', dot: '#fbbf24' },
    smile: { label: '😊 Smiling', color: '#34d399', dot: '#34d399' },
    serious: { label: '😐 Serious', color: '#64748b', dot: '#64748b' },
    nod: { label: '🤝 Nodding', color: '#a78bfa', dot: '#a78bfa' },
    shake: { label: '🙅 Shaking head', color: '#f87171', dot: '#f87171' },
    surprised: { label: '😲 Surprised', color: '#f87171', dot: '#f87171' },
    explaining: { label: '🗣 Explaining', color: '#818cf8', dot: '#818cf8' },
};

// ─── Keyword map: keywords → animState ───────────────────────────
const KEYWORD_MAP = [
    // Gestures – hands
    { keys: ['raise.*right hand', 'right hand up', 'right hand raise'], state: 'raiseRightHand' },
    { keys: ['raise.*left hand', 'left hand up', 'left hand raise'], state: 'raiseLeftHand' },
    { keys: ['lower.*right', 'right hand down'], state: 'lowerRightHand' },
    { keys: ['lower.*left', 'left hand down'], state: 'lowerLeftHand' },
    { keys: ['wave.*right', 'wave.*hand', 'wave'], state: 'waveRight' },
    { keys: ['fold.*hand', 'cross.*arm'], state: 'foldHands' },
    { keys: ['unfold.*hand', 'open.*arm'], state: 'idle' },

    // Board actions
    { keys: ['write on', 'writing on', 'chalk'], state: 'writeBoard' },
    { keys: ['underline', 'under line'], state: 'underline' },
    { keys: ['highlight', 'mark.*formula', 'circle.*equation'], state: 'highlight' },
    {
        keys: ['point.*board', 'point.*formula', 'point.*equation', 'point.*example',
            'pointing', 'indicate', 'show.*board', 'look.*board'], state: 'pointBoard'
    },

    // Expressions
    { keys: ['smile', 'happy', 'cheerful', 'grin'], state: 'smile' },
    { keys: ['serious', 'stern', 'focus'], state: 'serious' },
    { keys: ['surprised', 'wow', 'amazing', 'incredible', 'unexpected', 'shock'], state: 'surprised' },
    { keys: ['nod', 'agree', 'confirm', 'yes.*head'], state: 'nod' },
    { keys: ['shake.*head', 'disagree', 'no.*head'], state: 'shake' },

    // Teaching/explaining
    {
        keys: ['explain', 'describe', 'teach', 'demonstrate', 'clarify', 'elaborate',
            'step by step', 'summarize', 'summary', 'formula', 'equation', 'real.?life', 'example',
            'concept', 'definition', 'understand', 'because', 'therefore', 'thus', 'means',
            'important', 'note that', 'pay attention', 'listen', 'consider', 'think about',
            'first', 'second', 'third', 'next', 'then', 'finally', 'conclusion',
            'start explain', 'begin', 'introducing'], state: 'explaining'
    },

    // Board explanation (combined point + explain)
    { keys: ['look.*board.*explain', 'point.*explain', 'explain.*board'], state: 'pointBoard' },

    // Idle / reset
    {
        keys: ['idle', 'stand.*normal', 'reset.*all', 'return.*idle', 'stop.*explain',
            'stop.*talk', 'stand', 'face.*student', 'look.*forward'], state: 'idle'
    },
];

/**
 * Analyzes text content and returns the most relevant animation state.
 * Resolves compound commands (e.g. "smile and explain") by returning
 * the higher-priority action, then calling the secondary after a delay.
 */
export function analyzeContent(text) {
    if (!text) return ['idle'];
    const lower = text.toLowerCase();

    // Split compound "X and Y" commands
    const parts = lower.split(/\band\b|\bthen\b|\bwhile\b/);
    const matched = [];

    for (const part of parts) {
        const trimmed = part.trim();
        for (const { keys, state } of KEYWORD_MAP) {
            for (const k of keys) {
                if (new RegExp(k, 'i').test(trimmed)) {
                    if (!matched.includes(state)) matched.push(state);
                    break;
                }
            }
        }
    }

    return matched.length ? matched : ['idle'];
}

// ─────────────────────────────────────────────────────────────────
//  TEACHER AVATAR COMPONENT
// ─────────────────────────────────────────────────────────────────

export default function TeacherAvatar({ animState = 'idle', autoLabel = '', isSpeaking = false }) {
    const info = ANIMATION_STATES[animState] || ANIMATION_STATES.idle;

    // For timed animations (nod, shake) that auto-return to idle
    const [displayState, setDisplayState] = useState(animState);
    const resetRef = useRef(null);

    useEffect(() => {
        clearTimeout(resetRef.current);
        setDisplayState(animState);

        // Auto-return to 'explaining' after brief timed animations
        const timed = ['nod', 'shake', 'waveRight', 'surprised', 'raiseRightHand',
            'raiseLeftHand', 'lowerRightHand', 'lowerLeftHand'];
        if (timed.includes(animState)) {
            const returnState = isSpeaking ? 'explaining' : 'idle';
            resetRef.current = setTimeout(() => {
                setDisplayState(prev => prev === animState ? returnState : prev);
            }, animState === 'waveRight' ? 3200 : 2000);
        }
        return () => clearTimeout(resetRef.current);
    }, [animState, isSpeaking]);

    const stateInfo = ANIMATION_STATES[displayState] || ANIMATION_STATES.idle;

    return (
        <div className={`ta-wrap ta-${displayState}`}>
            {/* Auto-reaction label */}
            {autoLabel && (
                <div className="ta-auto-label" key={autoLabel}>⚡ {autoLabel}</div>
            )}

            {/* Base teacher image */}
            <img
                src={teacherImg}
                alt="Virtual Teacher"
                className="ta-image"
                draggable={false}
            />

            {/* ── Overlay: board highlight / underline ── */}
            <div className="ta-board-highlight" />

            {/* ── Overlay: talking mouth dots (shown when speaking) ── */}
            {(isSpeaking || displayState === 'explaining') && (
                <div className="ta-talk-dots">
                    <span /><span /><span />
                </div>
            )}

            {/* ── Overlay: expression emoji badges ── */}
            <div className="ta-overlay">
                {/* Smile overlay */}
                <svg className="ta-expression ta-smile-overlay" viewBox="0 0 80 40" fill="none">
                    <path d="M10 10 Q40 38 70 10" stroke="#34d399" strokeWidth="5"
                        strokeLinecap="round" fill="none" opacity="0.85" />
                    <circle cx="20" cy="8" r="4" fill="#34d399" opacity="0.7" />
                    <circle cx="60" cy="8" r="4" fill="#34d399" opacity="0.7" />
                </svg>

                {/* Serious overlay */}
                <svg className="ta-expression ta-serious-overlay" viewBox="0 0 80 40" fill="none">
                    <path d="M12 20 Q40 10 68 20" stroke="#94a3b8" strokeWidth="5"
                        strokeLinecap="round" fill="none" opacity="0.8" />
                    <line x1="18" y1="8" x2="30" y2="12" stroke="#94a3b8" strokeWidth="4"
                        strokeLinecap="round" opacity="0.7" />
                    <line x1="62" y1="8" x2="50" y2="12" stroke="#94a3b8" strokeWidth="4"
                        strokeLinecap="round" opacity="0.7" />
                </svg>

                {/* Surprised overlay */}
                <svg className="ta-expression ta-surprised-overlay" viewBox="0 0 80 60" fill="none">
                    <circle cx="40" cy="38" r="10" stroke="#f87171" strokeWidth="4" fill="none" />
                    <path d="M15 12 Q25 4 35 12" stroke="#f87171" strokeWidth="4"
                        strokeLinecap="round" fill="none" />
                    <path d="M65 12 Q55 4 45 12" stroke="#f87171" strokeWidth="4"
                        strokeLinecap="round" fill="none" />
                </svg>
            </div>

            {/* ── Status badge ── */}
            <div className="ta-badge" style={{ borderColor: `${stateInfo.color}55` }}>
                <span
                    className={`ta-badge-dot ${displayState !== 'idle' ? 'active' : ''}`}
                    style={{ '--dot-color': stateInfo.dot, background: stateInfo.dot }}
                />
                <span style={{ color: stateInfo.color }}>{stateInfo.label}</span>
            </div>
        </div>
    );
}
