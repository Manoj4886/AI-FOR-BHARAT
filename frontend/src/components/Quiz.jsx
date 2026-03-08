import { useState } from 'react';
import { generateQuiz, postProgress } from '../services/api';

const OPTION_COLORS = { A: '#6366F1', B: '#10B981', C: '#F59E0B', D: '#EF4444' };

export default function Quiz({ topic, skillLevel, userId, onClose }) {
    const [questions, setQuestions] = useState([]);
    const [current, setCurrent] = useState(0);
    const [selected, setSelected] = useState(null);
    const [revealed, setRevealed] = useState(false);
    const [score, setScore] = useState(0);
    const [finished, setFinished] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const startQuiz = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await generateQuiz(topic || 'General Knowledge', skillLevel, 5);
            setQuestions(data.questions);
            setCurrent(0);
            setScore(0);
            setSelected(null);
            setRevealed(false);
            setFinished(false);
        } catch (e) {
            setError('Failed to load quiz. Check your connection and try again.');
        }
        setLoading(false);
    };

    const handleSelect = (label) => {
        if (revealed) return;
        setSelected(label);
    };

    const handleReveal = () => {
        if (!selected) return;
        setRevealed(true);
        if (selected === questions[current].answer) {
            setScore(s => s + 1);
        }
    };

    const handleNext = async () => {
        if (current + 1 >= questions.length) {
            // finished
            setFinished(true);
            try {
                await postProgress(userId, 'quiz_completed', {
                    topic: topic || 'General Knowledge',
                    score: score + (selected === questions[current].answer ? 1 : 0),
                    total: questions.length,
                });
            } catch (_) { }
        } else {
            setCurrent(c => c + 1);
            setSelected(null);
            setRevealed(false);
        }
    };

    const finalScore = finished
        ? score + (selected === questions[current]?.answer ? 1 : 0)
        : score;

    if (loading) return (
        <div className="quiz-overlay">
            <div className="quiz-card">
                <div className="quiz-loading">
                    <div className="quiz-spinner" />
                    <p>Generating quiz on <strong>{topic}</strong>...</p>
                </div>
            </div>
        </div>
    );

    if (error) return (
        <div className="quiz-overlay">
            <div className="quiz-card">
                <p className="quiz-error">{error}</p>
                <button className="quiz-btn" onClick={startQuiz}>Retry</button>
                <button className="quiz-btn secondary" onClick={onClose}>Close</button>
            </div>
        </div>
    );

    if (questions.length === 0) return (
        <div className="quiz-overlay">
            <div className="quiz-card">
                <h2 className="quiz-title">📝 Quick Quiz</h2>
                <p className="quiz-subtitle">Test your understanding of <strong>{topic || 'General Knowledge'}</strong></p>
                <p className="quiz-meta">5 questions · {skillLevel} level</p>
                <div className="quiz-actions">
                    <button className="quiz-btn" onClick={startQuiz}>Start Quiz 🚀</button>
                    <button className="quiz-btn secondary" onClick={onClose}>Cancel</button>
                </div>
            </div>
        </div>
    );

    if (finished) {
        const pct = Math.round((finalScore / questions.length) * 100);
        const emoji = pct >= 80 ? '🏆' : pct >= 50 ? '👍' : '📚';
        return (
            <div className="quiz-overlay">
                <div className="quiz-card">
                    <div className="quiz-result-emoji">{emoji}</div>
                    <h2 className="quiz-title">Quiz Complete!</h2>
                    <div className="quiz-score-ring">
                        <svg viewBox="0 0 100 100" width="120" height="120">
                            <circle cx="50" cy="50" r="45" fill="none" stroke="#1e293b" strokeWidth="10" />
                            <circle cx="50" cy="50" r="45" fill="none" stroke="#6366F1" strokeWidth="10"
                                strokeDasharray={`${pct * 2.83} ${283 - pct * 2.83}`}
                                strokeDashoffset="70.75"
                                strokeLinecap="round"
                            />
                            <text x="50" y="55" textAnchor="middle" fill="white" fontSize="20" fontWeight="bold">{pct}%</text>
                        </svg>
                    </div>
                    <p className="quiz-score-text">{finalScore} / {questions.length} correct</p>
                    <div className="quiz-actions">
                        <button className="quiz-btn" onClick={startQuiz}>Retry 🔄</button>
                        <button className="quiz-btn secondary" onClick={onClose}>Done</button>
                    </div>
                </div>
            </div>
        );
    }

    const q = questions[current];
    return (
        <div className="quiz-overlay">
            <div className="quiz-card">
                <div className="quiz-progress-bar">
                    <div className="quiz-progress-fill" style={{ width: `${((current) / questions.length) * 100}%` }} />
                </div>
                <div className="quiz-header">
                    <span className="quiz-counter">Q{current + 1}/{questions.length}</span>
                    <span className="quiz-score-badge">Score: {score}</span>
                </div>
                <p className="quiz-question">{q.question}</p>
                <div className="quiz-options">
                    {q.options.map(opt => {
                        let cls = 'quiz-option';
                        if (revealed) {
                            if (opt.label === q.answer) cls += ' correct';
                            else if (opt.label === selected) cls += ' wrong';
                        } else if (opt.label === selected) cls += ' chosen';
                        return (
                            <button
                                key={opt.label}
                                className={cls}
                                style={{ '--option-color': OPTION_COLORS[opt.label] }}
                                onClick={() => handleSelect(opt.label)}
                            >
                                <span className="option-label">{opt.label}</span>
                                <span className="option-text">{opt.text}</span>
                            </button>
                        );
                    })}
                </div>
                <div className="quiz-actions">
                    {!revealed ? (
                        <button className="quiz-btn" onClick={handleReveal} disabled={!selected}>
                            Check Answer
                        </button>
                    ) : (
                        <>
                            <div className={`quiz-feedback ${selected === q.answer ? 'correct-msg' : 'wrong-msg'}`}>
                                {selected === q.answer ? '✅ Correct!' : `❌ Correct answer: ${q.answer}`}
                            </div>
                            <button className="quiz-btn" onClick={handleNext}>
                                {current + 1 >= questions.length ? 'Finish 🎉' : 'Next →'}
                            </button>
                        </>
                    )}
                    <button className="quiz-btn secondary" onClick={onClose}>Exit</button>
                </div>
            </div>
        </div>
    );
}
