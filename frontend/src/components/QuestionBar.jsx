import { useRef, useState } from 'react';

const LEVELS = [
    { id: 'beginner', icon: '🌱', label: 'Beginner', sub: 'Simple & Visual' },
    { id: 'intermediate', icon: '🔥', label: 'Intermediate', sub: 'Deep Dive' },
    { id: 'advanced', icon: '🚀', label: 'Advanced', sub: 'Technical' },
];

export default function QuestionBar({ onAsk, isLoading, skillLevel, onSkillChange, agentState, onListeningChange }) {
    const [question, setQuestion] = useState('');
    const [listening, setListening] = useState(false);
    const recogRef = useRef(null);

    const handleAsk = () => {
        if (!question.trim() || isLoading) return;
        onAsk(question.trim());
        setQuestion('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAsk();
        }
    };

    const startListening = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('Your browser does not support voice input. Try Chrome.');
            return;
        }
        const recog = new SpeechRecognition();
        recog.lang = 'en-US';
        recog.interimResults = true;
        recog.maxAlternatives = 1;
        recog.onresult = (e) => {
            const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
            setQuestion(transcript);
        };
        recog.onend = () => { setListening(false); onListeningChange?.(false); };
        recog.onerror = () => { setListening(false); onListeningChange?.(false); };
        recog.start();
        recogRef.current = recog;
        setListening(true);
        onListeningChange?.(true);
    };

    const stopListening = () => {
        recogRef.current?.stop();
        setListening(false);
        onListeningChange?.(false);
    };

    const isListeningMode = agentState === 'listening';

    return (
        <div className={`question-bar ${isListeningMode ? 'listening-mode' : ''}`}>
            {/* Skill level selector */}
            <div className="skill-selector">
                <span className="skill-label">Mode:</span>
                {LEVELS.map(lvl => (
                    <button
                        key={lvl.id}
                        className={`skill-btn ${skillLevel === lvl.id ? 'active' : ''}`}
                        onClick={() => onSkillChange(lvl.id)}
                        title={lvl.sub}
                    >
                        {lvl.icon} {lvl.label}
                        {skillLevel === lvl.id && <span className="skill-sub">{lvl.sub}</span>}
                    </button>
                ))}
            </div>

            {/* Input row */}
            <div className="input-row">
                <textarea
                    className={`question-input ${isListeningMode ? 'input-listening' : ''}`}
                    placeholder={
                        skillLevel === 'beginner'
                            ? '🌟 Ask me anything simply… e.g. What is gravity?'
                            : skillLevel === 'intermediate'
                                ? '🔥 Ask a deeper question… e.g. How does DNS work?'
                                : '🚀 Ask something technical… e.g. Explain Big O notation'
                    }
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => !listening && onListeningChange?.(false)}
                    rows={2}
                    disabled={isLoading}
                />
                <div className="input-actions">
                    <button
                        className={`mic-btn ${listening ? 'listening' : ''}`}
                        onClick={listening ? stopListening : startListening}
                        title={listening ? 'Stop listening' : 'Speak your question'}
                    >
                        {listening ? (
                            <div className="mic-waves">
                                <span /><span /><span />
                            </div>
                        ) : '🎤'}
                    </button>
                    <button
                        className="ask-btn"
                        onClick={handleAsk}
                        disabled={!question.trim() || isLoading}
                    >
                        {isLoading ? <span className="spinner" /> : <><span className="ask-arrow">➤</span> Ask</>}
                    </button>
                </div>
            </div>

            {/* Waveform hint when listening */}
            {listening && (
                <div className="listening-hint">
                    <div className="listen-bars">
                        {[...Array(8)].map((_, i) => (
                            <span key={i} style={{ animationDelay: `${i * 0.1}s` }} />
                        ))}
                    </div>
                    <span>Listening… speak your question</span>
                </div>
            )}
        </div>
    );
}
