import { useEffect, useRef, useState } from 'react';

const STATE_CONFIG = {
    idle: {
        label: '👨‍🏫 AI Tutor',
        badge: 'idle',
        borderColor: 'rgba(99,102,241,0.25)',
        glowColor: 'rgba(99,102,241,0.12)',
    },
    listening: {
        label: '🎙 Listening…',
        badge: 'listening',
        borderColor: 'rgba(16,185,129,0.6)',
        glowColor: 'rgba(16,185,129,0.18)',
    },
    thinking: {
        label: '💭 Thinking…',
        badge: 'thinking',
        borderColor: 'rgba(245,158,11,0.6)',
        glowColor: 'rgba(245,158,11,0.18)',
    },
    explaining: {
        label: '🗣 Explaining',
        badge: 'explaining',
        borderColor: 'rgba(99,102,241,0.8)',
        glowColor: 'rgba(99,102,241,0.28)',
    },
};

export default function CinematicAvatar({ agentState = 'idle', isSpeaking }) {
    const cfg = STATE_CONFIG[agentState] || STATE_CONFIG.idle;
    const [blinkClass, setBlinkClass] = useState('');
    const blinkTimer = useRef(null);

    // Random eye blink every 3-5s
    useEffect(() => {
        const scheduleBlink = () => {
            const delay = 3000 + Math.random() * 2000;
            blinkTimer.current = setTimeout(() => {
                setBlinkClass('blinking');
                setTimeout(() => setBlinkClass(''), 200);
                scheduleBlink();
            }, delay);
        };
        scheduleBlink();
        return () => clearTimeout(blinkTimer.current);
    }, []);

    return (
        <div className={`cinematic-avatar agent-${agentState}`}>
            {/* Thinking pulse rings */}
            {agentState === 'thinking' && (
                <div className="think-rings">
                    <div className="think-ring r1" />
                    <div className="think-ring r2" />
                    <div className="think-ring r3" />
                </div>
            )}

            {/* Glow backdrop */}
            <div
                className="avatar-glow-bg"
                style={{ '--glow': cfg.glowColor }}
            />

            {/* Portrait frame */}
            <div
                className={`avatar-portrait-frame ${blinkClass}`}
                style={{ '--border-col': cfg.borderColor }}
            >
                <img
                    src="/avatar.png"
                    alt="AI Tutor"
                    className="avatar-photo"
                    draggable={false}
                />

                {/* State overlay effects */}
                {agentState === 'listening' && (
                    <div className="listen-overlay">
                        <div className="ear-wave w1" />
                        <div className="ear-wave w2" />
                        <div className="ear-wave w3" />
                    </div>
                )}

                {agentState === 'explaining' && (
                    <div className="explain-hand">
                        <svg viewBox="0 0 60 80" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M30 70 C30 70 10 55 10 35 C10 20 20 12 30 12 C40 12 50 20 50 35 C50 55 30 70 30 70Z"
                                fill="rgba(99,102,241,0.18)"
                                stroke="rgba(99,102,241,0.5)"
                                strokeWidth="1.5"
                            />
                            <circle cx="30" cy="30" r="6" fill="rgba(99,102,241,0.6)" />
                        </svg>
                    </div>
                )}

                {/* Speaking jaw pulse overlay */}
                {isSpeaking && (
                    <div className="speaking-jaw-overlay">
                        <div className="jaw-pulse" />
                    </div>
                )}

                {/* Scan-line cinematic effect */}
                <div className="scanline" />
            </div>

            {/* Status badge */}
            <div className={`cinematic-badge badge-${cfg.badge}`}>
                <span className={`badge-dot dot-${cfg.badge}`} />
                {cfg.label}
            </div>

            {/* Speaking waveform */}
            {isSpeaking && (
                <div className="voice-waveform">
                    {[...Array(12)].map((_, i) => (
                        <span key={i} className="wave-bar" style={{ animationDelay: `${i * 0.08}s` }} />
                    ))}
                </div>
            )}
        </div>
    );
}
