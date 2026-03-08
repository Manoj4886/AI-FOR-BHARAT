import { useState, useEffect } from 'react';
import './AuthPage.css';

export default function AuthPage({ onLogin }) {
    const [mode, setMode] = useState('signin'); // 'signin' or 'signup'
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    // Clear errors when switching mode
    useEffect(() => { setError(''); }, [mode]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Validation
        if (mode === 'signup') {
            if (!name.trim()) return setError('Please enter your name');
            if (name.trim().length < 2) return setError('Name must be at least 2 characters');
        }
        if (!email.trim()) return setError('Please enter your email');
        if (!email.includes('@')) return setError('Please enter a valid email');
        if (password.length < 6) return setError('Password must be at least 6 characters');
        if (mode === 'signup' && password !== confirmPassword) {
            return setError('Passwords do not match');
        }

        setLoading(true);
        try {
            const endpoint = mode === 'signup' ? '/auth/register' : '/auth/login';
            const body = mode === 'signup'
                ? { name: name.trim(), email: email.trim(), password }
                : { email: email.trim(), password };

            const res = await fetch(`${BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            const data = await res.json();

            if (!res.ok) {
                setError(data.detail || 'Something went wrong');
                setLoading(false);
                return;
            }

            // Save session to localStorage
            localStorage.setItem('saarathi_token', data.token);
            localStorage.setItem('saarathi_user', JSON.stringify({
                name: data.name,
                email: data.email,
            }));

            // Call parent callback
            onLogin({ name: data.name, email: data.email, token: data.token });
        } catch (err) {
            setError('Cannot connect to server. Make sure the backend is running.');
        }
        setLoading(false);
    };

    return (
        <div className="auth-page">
            {/* Animated background */}
            <div className="auth-bg">
                <div className="auth-orb auth-orb-1" />
                <div className="auth-orb auth-orb-2" />
                <div className="auth-orb auth-orb-3" />
            </div>

            <div className="auth-container">
                {/* Brand */}
                <div className="auth-brand">
                    <div className="auth-logo">
                        <span className="auth-logo-icon">⬡</span>
                    </div>
                    <h1 className="auth-title">Saar<span className="auth-accent">athi</span></h1>
                    <p className="auth-subtitle">Your AI-Powered Learning Companion</p>
                </div>

                {/* Card */}
                <div className="auth-card">
                    {/* Tab switcher */}
                    <div className="auth-tabs">
                        <button
                            className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
                            onClick={() => setMode('signin')}
                        >
                            Sign In
                        </button>
                        <button
                            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
                            onClick={() => setMode('signup')}
                        >
                            Sign Up
                        </button>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {/* Name field (signup only) */}
                        {mode === 'signup' && (
                            <div className="auth-field">
                                <label className="auth-label">Full Name</label>
                                <div className="auth-input-wrap">
                                    <span className="auth-input-icon">👤</span>
                                    <input
                                        type="text"
                                        className="auth-input"
                                        placeholder="Enter your name"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        autoComplete="name"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Email */}
                        <div className="auth-field">
                            <label className="auth-label">Email Address</label>
                            <div className="auth-input-wrap">
                                <span className="auth-input-icon">📧</span>
                                <input
                                    type="email"
                                    className="auth-input"
                                    placeholder="you@example.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    autoComplete="email"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="auth-field">
                            <label className="auth-label">Password</label>
                            <div className="auth-input-wrap">
                                <span className="auth-input-icon">🔒</span>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    className="auth-input"
                                    placeholder="Min. 6 characters"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                                />
                                <button
                                    type="button"
                                    className="auth-eye-btn"
                                    onClick={() => setShowPassword(v => !v)}
                                    tabIndex={-1}
                                >
                                    {showPassword ? '🙈' : '👁️'}
                                </button>
                            </div>
                        </div>

                        {/* Confirm Password (signup only) */}
                        {mode === 'signup' && (
                            <div className="auth-field">
                                <label className="auth-label">Confirm Password</label>
                                <div className="auth-input-wrap">
                                    <span className="auth-input-icon">🔒</span>
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        className="auth-input"
                                        placeholder="Re-enter your password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        autoComplete="new-password"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="auth-error">
                                <span>⚠️</span> {error}
                            </div>
                        )}

                        {/* Submit */}
                        <button className="auth-submit" type="submit" disabled={loading}>
                            {loading ? (
                                <span className="auth-spinner" />
                            ) : mode === 'signin' ? (
                                '🚀 Sign In'
                            ) : (
                                '✨ Create Account'
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="auth-footer">
                        {mode === 'signin' ? (
                            <p>Don't have an account? <button className="auth-link" onClick={() => setMode('signup')}>Sign up</button></p>
                        ) : (
                            <p>Already have an account? <button className="auth-link" onClick={() => setMode('signin')}>Sign in</button></p>
                        )}
                    </div>
                </div>

                {/* Features preview */}
                <div className="auth-features">
                    <div className="auth-feature">
                        <span className="auth-feature-icon">🎓</span>
                        <span>AI-Powered Teaching</span>
                    </div>
                    <div className="auth-feature">
                        <span className="auth-feature-icon">💻</span>
                        <span>Code in 20+ Languages</span>
                    </div>
                    <div className="auth-feature">
                        <span className="auth-feature-icon">🎨</span>
                        <span>Visual Explanations</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
