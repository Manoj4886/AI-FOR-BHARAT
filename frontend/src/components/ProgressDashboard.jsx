import { useEffect, useState } from 'react';
import { getProgress } from '../services/api';
import {
    LineChart, Line, BarChart, Bar, XAxis, YAxis,
    CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const SKILL_BADGES = {
    beginner: { color: '#10B981', icon: '🌱', label: 'Beginner' },
    intermediate: { color: '#F59E0B', icon: '🔥', label: 'Intermediate' },
    advanced: { color: '#6366F1', icon: '🚀', label: 'Advanced' },
};

function CustomTooltip({ active, payload, label }) {
    if (active && payload && payload.length) {
        return (
            <div className="chart-tooltip">
                <p>{label}</p>
                {payload.map(p => (
                    <p key={p.name} style={{ color: p.color }}>{p.name}: {p.value}</p>
                ))}
            </div>
        );
    }
    return null;
}

export default function ProgressDashboard({ userId }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadProgress = async () => {
        setLoading(true);
        try {
            const p = await getProgress(userId);
            setData(p);
        } catch (e) {
            setError('Could not load progress. Make sure you have asked at least one question.');
        }
        setLoading(false);
    };

    useEffect(() => { loadProgress(); }, [userId]);

    if (loading) return (
        <div className="progress-loading">
            <div className="quiz-spinner" />
            <p>Loading your progress...</p>
        </div>
    );

    if (error) return (
        <div className="progress-error">
            <p>{error}</p>
            <button className="quiz-btn" onClick={loadProgress}>Retry</button>
        </div>
    );

    const badge = SKILL_BADGES[data?.skill_level || 'beginner'];

    // Quiz performance chart data
    const quizChartData = (data?.quiz_scores || [])
        .slice(0, 10)
        .reverse()
        .map((s, i) => ({
            name: `#${i + 1} ${s.topic?.slice(0, 12)}`,
            score: s.total ? Math.round((s.score / s.total) * 100) : 0,
            raw: `${s.score}/${s.total}`,
        }));

    // Questions per topic
    const recentQs = data?.recent_questions || [];
    const topicCount = {};
    recentQs.forEach(q => {
        const lvl = q.skill_level || 'beginner';
        topicCount[lvl] = (topicCount[lvl] || 0) + 1;
    });
    const levelData = Object.entries(topicCount).map(([level, count]) => ({ level, count }));

    return (
        <div className="progress-dashboard">
            {/* Stats row */}
            <div className="stats-row">
                <div className="stat-card">
                    <div className="stat-icon">❓</div>
                    <div className="stat-value">{data?.questions_asked || 0}</div>
                    <div className="stat-label">Questions Asked</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">📝</div>
                    <div className="stat-value">{data?.quiz_scores?.length || 0}</div>
                    <div className="stat-label">Quizzes Taken</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">{badge.icon}</div>
                    <div className="stat-value" style={{ color: badge.color }}>{badge.label}</div>
                    <div className="stat-label">Current Level</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🎯</div>
                    <div className="stat-value">
                        {quizChartData.length > 0
                            ? `${Math.round(quizChartData.reduce((a, b) => a + b.score, 0) / quizChartData.length)}%`
                            : '—'}
                    </div>
                    <div className="stat-label">Avg Quiz Score</div>
                </div>
            </div>

            {/* Quiz scores chart */}
            {quizChartData.length > 0 ? (
                <div className="chart-card">
                    <h3 className="chart-title">📊 Quiz Performance</h3>
                    <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={quizChartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis tick={{ fill: '#94a3b8' }} domain={[0, 100]} unit="%" />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="score" fill="#6366F1" radius={[6, 6, 0, 0]} name="Score %" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            ) : (
                <div className="chart-card empty-chart">
                    <p>📝 Take a quiz to see your performance chart!</p>
                </div>
            )}

            {/* Questions by level */}
            {levelData.length > 0 && (
                <div className="chart-card">
                    <h3 className="chart-title">📚 Questions by Skill Level</h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={levelData} layout="vertical" margin={{ left: 40, right: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis type="number" tick={{ fill: '#94a3b8' }} />
                            <YAxis type="category" dataKey="level" tick={{ fill: '#94a3b8' }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" fill="#10B981" radius={[0, 6, 6, 0]} name="Questions" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Recent questions */}
            {recentQs.length > 0 && (
                <div className="chart-card">
                    <h3 className="chart-title">🕐 Recent Questions</h3>
                    <ul className="recent-questions">
                        {recentQs.slice(0, 8).map((q, i) => (
                            <li key={i} className="recent-q-item">
                                <span className="recent-q-text">{q.question}</span>
                                <span className={`skill-pill ${q.skill_level}`}>{q.skill_level}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
