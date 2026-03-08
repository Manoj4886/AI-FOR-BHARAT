import { useRef, useState } from 'react';
import { analyzeContent } from './TeacherAvatar';

// ─── Quick-command chip groups ────────────────────────────────────
const CHIP_GROUPS = [
    {
        label: '🤚 Gestures',
        chips: [
            'Raise your right hand',
            'Raise your left hand',
            'Wave your right hand',
            'Fold your hands',
            'Lower your right hand',
        ],
    },
    {
        label: '😊 Expressions',
        chips: ['Smile', 'Look serious', 'Nod your head', 'Shake your head', 'Look surprised'],
    },
    {
        label: '📋 Board',
        chips: [
            'Point at the board',
            'Point to the formula',
            'Write on the board',
            'Underline the equation',
            'Highlight the formula',
        ],
    },
    {
        label: '🗣 Teaching',
        chips: [
            'Start explaining',
            'Explain the formula',
            'Explain step by step',
            'Give a real-life example',
            'Summarize the topic',
            'Stop explaining',
            'Reset all actions',
        ],
    },
];

export default function TeacherCommandPanel({ onCommand, currentState, isListening, onListeningChange }) {
    const [input, setInput] = useState('');
    const [voiceListening, setVoiceListening] = useState(false);
    const recogRef = useRef(null);

    const submit = (text) => {
        const t = text.trim();
        if (!t) return;
        onCommand(t);
        setInput('');
    };

    const handleKey = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(input); }
    };

    const startVoice = () => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { alert('Voice input requires Chrome or Edge.'); return; }
        const recog = new SR();
        recog.lang = 'en-US';
        recog.interimResults = true;
        recog.maxAlternatives = 1;
        recog.onresult = (e) => {
            const t = Array.from(e.results).map(r => r[0].transcript).join('');
            setInput(t);
        };
        recog.onend = () => {
            setVoiceListening(false);
            onListeningChange?.(false);
            // Auto-submit what was heard
            setInput(prev => { if (prev.trim()) onCommand(prev.trim()); return ''; });
        };
        recog.onerror = () => { setVoiceListening(false); onListeningChange?.(false); };
        recog.start();
        recogRef.current = recog;
        setVoiceListening(true);
        onListeningChange?.(true);
    };

    const stopVoice = () => {
        recogRef.current?.stop();
        setVoiceListening(false);
        onListeningChange?.(false);
    };

    return (
        <div className="tcp-wrap">
            {/* Header */}
            <div className="tcp-header">
                <span className="tcp-title">🎙 Command Center</span>
                <span className="tcp-hint">Type, speak, or tap a command — the teacher reacts automatically</span>
            </div>

            {/* Input row */}
            <div className="tcp-input-row">
                <input
                    className={`tcp-input ${voiceListening ? 'tcp-listening' : ''}`}
                    placeholder={voiceListening
                        ? '🎤 Listening… speak your command'
                        : 'Type a command or question… (e.g. "Explain step by step and smile")'}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKey}
                />
                <button
                    className={`tcp-mic-btn ${voiceListening ? 'tcp-mic-active' : ''}`}
                    onClick={voiceListening ? stopVoice : startVoice}
                    title={voiceListening ? 'Stop listening' : 'Speak command'}
                >
                    {voiceListening
                        ? <span className="tcp-mic-waves"><span /><span /><span /></span>
                        : '🎤'}
                </button>
                <button
                    className="tcp-send-btn"
                    onClick={() => submit(input)}
                    disabled={!input.trim()}
                >
                    ➤ Send
                </button>
            </div>

            {/* Voice listening indicator */}
            {voiceListening && (
                <div className="tcp-voice-bar">
                    {[...Array(10)].map((_, i) => (
                        <span key={i} className="tcp-vbar" style={{ animationDelay: `${i * 0.09}s` }} />
                    ))}
                    <span className="tcp-voice-label">Listening… speak now</span>
                </div>
            )}

            {/* Quick command chips */}
            <div className="tcp-chips-wrap">
                {CHIP_GROUPS.map(group => (
                    <div key={group.label} className="tcp-chip-group">
                        <span className="tcp-group-label">{group.label}</span>
                        <div className="tcp-chips">
                            {group.chips.map(cmd => (
                                <button
                                    key={cmd}
                                    className={`tcp-chip ${analyzeContent(cmd)[0] === currentState ? 'tcp-chip-active' : ''}`}
                                    onClick={() => submit(cmd)}
                                >
                                    {cmd}
                                </button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
