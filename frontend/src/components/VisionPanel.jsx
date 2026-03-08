import { useState, useRef, useEffect } from 'react';
import { generateVideo } from '../services/api';

/**
 * VisionPanel — Displays an AI-generated image or Polly-narrated video.
 *
 * Props:
 *   visualScene {string}  – Topic / scene description for image generation
 *   topic       {string}  – Topic name for display
 *   spokenText  {string}  – Spoken explanation (used in video captions)
 *   trigger     {number}  – Increment this to start a new generation cycle
 *   apiVideo    {string}  – base64 MP4 from the API (auto-plays when set)
 *   rekLabels   {Array}   – Rekognition labels detected from uploaded image
 */

/** Extract clean keywords from a prompt for Picsum seed */
function promptToSeed(prompt) {
    // Hash the prompt to get a deterministic Picsum image
    let hash = 0;
    for (let i = 0; i < prompt.length; i++) {
        hash = ((hash << 5) - hash) + prompt.charCodeAt(i);
        hash |= 0;
    }
    return Math.abs(hash) % 1000;
}

/** Build a Picsum URL based on the topic */
function buildPicsumUrl(prompt, width = 640, height = 400) {
    const seed = promptToSeed(prompt);
    return `https://picsum.photos/seed/${seed}/${width}/${height}`;
}

export default function VisionPanel({ visualScene, topic, spokenText, trigger, apiVideo, rekLabels }) {
    const [phase, setPhase] = useState('idle');
    const [imageUrl, setImageUrl] = useState(null);    // Picsum URL
    const [imageB64, setImageB64] = useState(null);    // Backend base64 fallback
    const [videoB64, setVideoB64] = useState(null);
    const [imgSource, setImgSource] = useState('');
    const [errorMsg, setErrorMsg] = useState('');
    const [videoVisible, setVideoVisible] = useState(false);
    const [imgLoaded, setImgLoaded] = useState(false);
    const videoRef = useRef(null);
    const abortRef = useRef(false);

    // ── Auto-play API video when backend provides it ────────────────────────
    useEffect(() => {
        if (!apiVideo) return;
        setVideoB64(apiVideo);
        setPhase('vid-ready');
        setVideoVisible(true);
        setImgSource('aws-polly');
    }, [apiVideo]);

    useEffect(() => {
        if (!visualScene || trigger === 0) return;

        abortRef.current = false;
        setPhase('img-loading');
        setImageUrl(null);
        setImageB64(null);
        setVideoB64(null);
        setVideoVisible(false);
        setImgLoaded(false);
        setErrorMsg('');

        // Try Picsum first (deterministic, free, no key)
        const url = buildPicsumUrl(visualScene);
        setImageUrl(url);
        setImgSource('picsum');

        return () => { abortRef.current = true; };
    }, [trigger]);

    // ── Fallback: backend /vision/generate-image ────────────────────────────
    const handleImgError = async () => {
        if (abortRef.current) return;
        setImgLoaded(false);
        setImageUrl(null);

        try {
            const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const res = await fetch(`${BASE}/vision/generate-image`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: visualScene }),
            });
            const data = await res.json();
            if (!abortRef.current) {
                setImageB64(data.image_b64);
                setImgSource(data.source || 'backend');
                setPhase('img-ready');
            }
        } catch {
            if (!abortRef.current) {
                setErrorMsg('Image generation failed. Check backend or network.');
                setPhase('error');
            }
        }
    };

    const handleImgLoad = () => {
        setImgLoaded(true);
        setPhase('img-ready');
    };

    // ── Video generation ────────────────────────────────────────────────────
    const handleGenerateVideo = async () => {
        if (!imageB64 && !imageUrl) return;
        setPhase('vid-loading');
        try {
            let b64 = imageB64;
            if (!b64 && imageUrl) {
                const resp = await fetch(imageUrl);
                const blob = await resp.blob();
                b64 = await new Promise(resolve => {
                    const reader = new FileReader();
                    reader.onload = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(blob);
                });
            }
            const res = await generateVideo(b64, topic, spokenText);
            setVideoB64(res.video_b64);
            setPhase('vid-ready');
            setTimeout(() => setVideoVisible(true), 50);
        } catch {
            setErrorMsg('Video generation failed.');
            setPhase('img-ready');
        }
    };

    useEffect(() => {
        if (videoVisible && videoRef.current && videoB64) {
            const bytes = Uint8Array.from(atob(videoB64), c => c.charCodeAt(0));
            const blob = new Blob([bytes], { type: 'video/mp4' });
            videoRef.current.src = URL.createObjectURL(blob);
            videoRef.current.play();
        }
    }, [videoVisible, videoB64]);

    const BADGES = {
        picsum: { label: '📸 Visual', style: { background: 'rgba(30,64,175,0.8)', color: '#93c5fd' } },
        pollinations: { label: '✨ AI Generated', style: { background: 'linear-gradient(90deg,#7c3aed,#2563eb)', color: '#fff' } },
        bedrock: { label: '✨ Bedrock AI', style: { background: 'linear-gradient(90deg,#0369a1,#0284c7)', color: '#fff' } },
        'aws-polly': { label: '🎥 AWS Video · Polly', style: { background: 'linear-gradient(90deg,#b45309,#d97706)', color: '#fff' } },
        placeholder: { label: 'Preview', style: {} },
    };
    const badge = BADGES[imgSource] || {};

    if (phase === 'idle' && !apiVideo) return null;

    return (
        <div className="vision-panel">
            {/* Header */}
            <div className="vision-header">
                <span className="vision-icon">🎨</span>
                <span className="vision-title">AI Visual</span>
                {badge.label && (
                    <span className="vision-badge vision-badge--ai" style={badge.style}>
                        {badge.label}
                    </span>
                )}
            </div>

            {/* Image area */}
            <div className="vision-img-wrap" style={{ position: 'relative' }}>
                {/* Loading skeleton */}
                {(phase === 'img-loading' || (imageUrl && !imgLoaded)) && (
                    <div className="vision-skeleton">
                        <div className="vision-skeleton-shimmer" />
                        <span className="vision-skeleton-label">
                            {phase === 'img-loading' ? 'Finding visual…' : 'Loading image…'}
                        </span>
                    </div>
                )}

                {/* Picsum / Pollinations direct URL */}
                {imageUrl && !videoVisible && (
                    <div style={{ position: 'relative', display: imgLoaded ? 'block' : 'none' }}>
                        <img
                            className="vision-img"
                            src={imageUrl}
                            alt={`Visual: ${topic}`}
                            onLoad={handleImgLoad}
                            onError={handleImgError}
                            style={{ width: '100%', borderRadius: '8px', display: 'block' }}
                        />
                        {/* Topic overlay on the photo */}
                        {imgLoaded && topic && (
                            <div style={{
                                position: 'absolute',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                padding: '20px 16px 12px',
                                background: 'linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)',
                                color: '#fff',
                                fontWeight: 700,
                                fontSize: '15px',
                                borderRadius: '0 0 8px 8px',
                                letterSpacing: '0.02em',
                            }}>
                                {topic.length > 80 ? topic.slice(0, 80) + '…' : topic}
                            </div>
                        )}
                    </div>
                )}

                {/* Backend base64 fallback */}
                {!imageUrl && imageB64 && !videoVisible && (
                    <img
                        className="vision-img"
                        src={`data:image/png;base64,${imageB64}`}
                        alt={`Visual: ${topic}`}
                        style={{ width: '100%', borderRadius: '8px' }}
                    />
                )}

                {/* Video player */}
                {videoVisible && videoB64 && (
                    <video ref={videoRef} className="vision-video" controls loop playsInline />
                )}

                {/* Error */}
                {phase === 'error' && (
                    <div className="vision-error">
                        <span>⚠️</span>
                        <p>{errorMsg}</p>
                    </div>
                )}
            </div>

            {/* Action buttons */}
            {phase === 'img-ready' && (
                <div className="vision-actions">
                    <button className="vision-btn vision-btn--video" onClick={handleGenerateVideo}>
                        🎬 Generate Video
                    </button>
                </div>
            )}

            {phase === 'vid-loading' && (
                <div className="vision-actions">
                    <button className="vision-btn vision-btn--video vision-btn--loading" disabled>
                        <span className="vision-spinner" /> Rendering Video…
                    </button>
                </div>
            )}

            {phase === 'vid-ready' && (
                <div className="vision-actions">
                    <button className="vision-btn vision-btn--outline"
                        onClick={() => { setVideoVisible(false); setPhase('img-ready'); }}>
                        🖼 Show Image
                    </button>
                    <button className="vision-btn vision-btn--video" onClick={() => setVideoVisible(true)}>
                        ▶ Play Video
                    </button>
                </div>
            )}

            {/* Amazon Rekognition labels badge strip */}
            {rekLabels && rekLabels.length > 0 && (
                <div style={{
                    padding: '8px 14px 4px',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '6px',
                    borderTop: '1px solid rgba(251,191,36,0.15)',
                }}>
                    <span style={{ fontSize: '11px', color: '#fbbf24', fontWeight: 600, width: '100%', marginBottom: '2px' }}>🔍 Rekognition detected:</span>
                    {rekLabels.map((lbl, i) => (
                        <span key={i} style={{
                            background: 'rgba(251,191,36,0.12)',
                            border: '1px solid rgba(251,191,36,0.3)',
                            borderRadius: '12px',
                            padding: '2px 10px',
                            fontSize: '11px',
                            color: '#fde68a',
                        }}>{lbl}</span>
                    ))}
                </div>
            )}

            {/* Topic label */}
            {topic && (
                <div className="vision-topic-label">
                    <span className="vision-topic-dot" />
                    {topic}
                </div>
            )}
        </div>
    );
}
