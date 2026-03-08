import { useEffect, useRef, useState } from 'react';

const BEGINNER_ICONS = ['🌟', '💡', '📖', '🎯', '🔮', '✨', '🚀', '🌈'];

function splitIntoBullets(text) {
    if (!text) return [];
    const lines = text.split(/\n+/).filter(Boolean);
    if (lines.length > 1) return lines;
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    const bullets = [];
    for (let i = 0; i < sentences.length; i += 2) {
        bullets.push((sentences[i] + (sentences[i + 1] || '')).trim());
    }
    return bullets;
}

// Renders explanation text with *gesture cues* highlighted
function StyledExplanation({ text }) {
    if (!text) return null;
    const parts = text.split(/(\*[^*]+\*)/g);
    return (
        <span>
            {parts.map((part, i) =>
                part.startsWith('*') && part.endsWith('*')
                    ? <em key={i} className="gesture-cue">{part.slice(1, -1)}</em>
                    : <span key={i}>{part}</span>
            )}
        </span>
    );
}

function WriteOnText({ text, active }) {
    const [revealed, setRevealed] = useState(0);
    const bullets = splitIntoBullets(text);

    useEffect(() => {
        if (!active || !text) { setRevealed(0); return; }
        setRevealed(0);
        let i = 0;
        const interval = setInterval(() => {
            i++;
            setRevealed(i);
            if (i >= bullets.length) clearInterval(interval);
        }, 420);
        return () => clearInterval(interval);
    }, [text, active]);

    return (
        <div className="write-on-container">
            {bullets.map((bullet, idx) => (
                <div
                    key={idx}
                    className={`write-on-line ${idx < revealed ? 'line-visible' : 'line-hidden'}`}
                    style={{ transitionDelay: `${idx * 0.05}s` }}
                >
                    <span className="neon-cursor-dot">▸</span>
                    <span><StyledExplanation text={bullet} /></span>
                </div>
            ))}
        </div>
    );
}

// Visual Scene card — rendered below explanation
function VisualSceneCard({ scene }) {
    if (!scene) return null;
    return (
        <div className="visual-scene-card">
            <div className="vs-header">
                <span className="vs-icon">🎬</span>
                <span className="vs-title">Visual Scene</span>
            </div>
            <p className="vs-body">{scene}</p>
        </div>
    );
}

// Flow diagram card
function FlowDiagramCard({ diagram }) {
    if (!diagram) return null;
    return (
        <div className="flow-diagram-card">
            <div className="vs-header">
                <span className="vs-icon">🔀</span>
                <span className="vs-title">Flow</span>
            </div>
            <pre className="flow-pre">{diagram}</pre>
        </div>
    );
}

function BeginnerBoard({ text, visualScene, flowDiagram, isThinking }) {
    const bullets = splitIntoBullets(text);
    return (
        <div className="board-beginner">
            {isThinking ? (
                <div className="board-skeleton">
                    <div className="skel-line wide" /><div className="skel-line med" /><div className="skel-line wide" />
                </div>
            ) : bullets.map((b, i) => (
                <div key={i} className="beginner-card" style={{ animationDelay: `${i * 0.18}s` }}>
                    <span className="beginner-icon">{BEGINNER_ICONS[i % BEGINNER_ICONS.length]}</span>
                    <p className="beginner-text"><StyledExplanation text={b} /></p>
                </div>
            ))}
            {!isThinking && <><VisualSceneCard scene={visualScene} /><FlowDiagramCard diagram={flowDiagram} /></>}
        </div>
    );
}

function IntermediateBoard({ text, visualScene, flowDiagram, isThinking }) {
    const bullets = splitIntoBullets(text);
    const half = Math.ceil(bullets.length / 2);
    const prose = bullets.slice(0, half);
    const code = bullets.slice(half);
    return (
        <div className="board-intermediate">
            <div className="inter-panel inter-prose">
                <div className="inter-label">📝 Explanation</div>
                {isThinking ? <div className="board-skeleton"><div className="skel-line wide" /><div className="skel-line med" /></div>
                    : <WriteOnText text={prose.join('\n')} active={!isThinking} />}
            </div>
            <div className="inter-divider" />
            <div className="inter-panel inter-code">
                <div className="inter-label">💻 Key Points</div>
                {isThinking ? <div className="board-skeleton"><div className="skel-line med" /><div className="skel-line wide" /></div>
                    : <div className="code-block">{code.map((l, i) => <div key={i} className="code-line"><span className="code-num">{i + 1}</span>{l}</div>)}</div>}
            </div>
            {!isThinking && (
                <div className="inter-extras">
                    <VisualSceneCard scene={visualScene} />
                    <FlowDiagramCard diagram={flowDiagram} />
                </div>
            )}
        </div>
    );
}

function AdvancedBoard({ text, visualScene, flowDiagram, isThinking }) {
    const bullets = splitIntoBullets(text);
    return (
        <div className="board-advanced">
            {isThinking ? (
                <div className="board-skeleton adv">
                    <div className="skel-line wide" /><div className="skel-line med" /><div className="skel-line wide" /><div className="skel-line med" />
                </div>
            ) : (
                <>
                    <div className="adv-code-view">
                        <div className="adv-code-header">
                            <span className="adv-badge">◉ Analysis</span>
                            <span className="adv-lang">AI · Explanation</span>
                        </div>
                        {bullets.map((b, i) => (
                            <div key={i} className="adv-code-line" style={{ animationDelay: `${i * 0.12}s` }}>
                                <span className="adv-ln">{String(i + 1).padStart(2, '0')}</span>
                                <span className="adv-kw">{i === 0 ? 'CORE:' : i % 3 === 0 ? 'NOTE:' : ''}</span>
                                <span><StyledExplanation text={b} /></span>
                            </div>
                        ))}
                    </div>
                    <VisualSceneCard scene={visualScene} />
                    <FlowDiagramCard diagram={flowDiagram} />
                </>
            )}
        </div>
    );
}

export default function GlassBoard({ text, visualScene, flowDiagram, agentState, skillLevel }) {
    // Show board when: thinking, explaining, OR already has content (keep visible after speaking)
    const hasContent = Boolean(text);
    const visible = agentState === 'thinking' || agentState === 'explaining' || hasContent;
    const isThinking = agentState === 'thinking';
    const [mounted, setMounted] = useState(false);
    const [animOut, setAnimOut] = useState(false);
    const prevVisible = useRef(false);

    useEffect(() => {
        if (visible && !prevVisible.current) {
            setAnimOut(false);
            setMounted(true);
        } else if (!visible && prevVisible.current) {
            setAnimOut(true);
            const t = setTimeout(() => setMounted(false), 350);
            return () => clearTimeout(t);
        }
        prevVisible.current = visible;
    }, [visible]);

    if (!mounted) return null;

    return (
        <div className={`glass-board skill-${skillLevel} ${animOut ? 'board-exit' : 'board-enter'}`}>
            {/* Neon top bar */}
            <div className="board-neon-bar" />

            {/* Header */}
            <div className="board-header">
                <div className="board-dots">
                    <span className="bdot red" /><span className="bdot yellow" /><span className="bdot green" />
                </div>
                <span className="board-title">
                    {isThinking ? '⚡ Thinking…' : skillLevel === 'beginner' ? '📖 Let\'s Learn!' : skillLevel === 'intermediate' ? '🔥 Deep Dive' : '🚀 Technical Analysis'}
                </span>
                <div className="board-level-badge">{skillLevel}</div>
            </div>

            {/* Content by skill level */}
            <div className="board-body">
                {skillLevel === 'beginner' && <BeginnerBoard text={text} visualScene={visualScene} flowDiagram={flowDiagram} isThinking={isThinking} />}
                {skillLevel === 'intermediate' && <IntermediateBoard text={text} visualScene={visualScene} flowDiagram={flowDiagram} isThinking={isThinking} />}
                {skillLevel === 'advanced' && <AdvancedBoard text={text} visualScene={visualScene} flowDiagram={flowDiagram} isThinking={isThinking} />}
            </div>

            {/* Corner sparkle */}
            <div className="board-sparkle tl" />
            <div className="board-sparkle br" />
        </div>
    );
}
