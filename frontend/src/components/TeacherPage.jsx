import { useState, useEffect, useRef, useCallback } from 'react';
import Avatar from './Avatar';
import MermaidDiagram from './MermaidDiagram';
import VisionPanel from './VisionPanel';
import Quiz from './Quiz';
import { askQuestion, askQuestionWithFile } from '../services/api';
import { wordToViseme } from './AvatarModel';

// ─── Animation analysis (moved from TeacherAvatar) ─────────────────
const GESTURE_KEYWORDS = [
    { keys: ['write on', 'writing on', 'chalk'], state: 'writeBoard' },
    { keys: ['point.*board', 'point.*formula', 'point.*equation', 'point.*example', 'pointing', 'indicate', 'show.*board', 'look.*board'], state: 'pointBoard' },
    { keys: ['explain', 'describe', 'teach', 'demonstrate', 'clarify', 'elaborate', 'step by step', 'summarize', 'formula', 'equation', 'real.?life', 'example', 'concept', 'definition', 'understand', 'because', 'therefore', 'thus', 'means', 'important', 'first', 'second', 'third', 'next', 'then', 'finally', 'conclusion'], state: 'explaining' },
    { keys: ['smile', 'happy', 'cheerful', 'grin'], state: 'smile' },
    { keys: ['nod', 'agree', 'confirm', 'yes.*head'], state: 'nod' },
    { keys: ['shake.*head', 'disagree', 'no.*head'], state: 'shake' },
    { keys: ['serious', 'stern', 'focus'], state: 'serious' },
    { keys: ['surprised', 'wow', 'amazing', 'incredible', 'unexpected', 'shock'], state: 'surprised' },
];

function analyzeContent(text) {
    if (!text) return ['idle'];
    const lower = text.toLowerCase();
    const parts = lower.split(/\band\b|\bthen\b|\bwhile\b/);
    const matched = [];
    for (const part of parts) {
        const trimmed = part.trim();
        for (const { keys, state } of GESTURE_KEYWORDS) {
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

// ─── Unique session user ID ────────────────────────────────────────
const SESSION_ID = 'teacher_' + Math.random().toString(36).slice(2, 8);

// ─── Decode & play base64 MP3 ─────────────────────────────────────
async function decodeAndPlay(base64, onEnded) {
    const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
    const ctx = new AudioContext();
    const buf = await ctx.decodeAudioData(bytes.buffer);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    src.start(0);
    src.onended = () => { ctx.close(); onEnded?.(); };
    return src;
}

// ─── Derive animation states from question + answer ────────────────
// Builds a rich animation sequence that mirrors the teaching content
function buildAnimSequence(question, answer) {
    const seq = [];

    // Always react to incoming question first
    if (/formula|equation|theorem|proof|math|calculate|compute/i.test(question)) {
        seq.push('pointBoard');
    } else if (/what|how|why|explain|describe|tell me/i.test(question)) {
        seq.push('nod');
    } else if (/example|real.?life|show/i.test(question)) {
        seq.push('smile');
    }

    // Read keywords from the answer for the main teaching sequence
    const lower = answer.toLowerCase();
    const states = analyzeContent(answer);

    // Build a varied sequence (max 6 states, no back-to-back duplicates)
    const answerStates = states.filter(s => s !== 'idle');
    const mixed = [];

    // 1. Greeting / acknowledgment
    mixed.push('smile');

    // 2. Primary content states (from answer analysis, up to 4)
    for (const s of answerStates.slice(0, 4)) {
        if (mixed[mixed.length - 1] !== s) mixed.push(s);
    }

    // 3. Board-related: if answer has formula/step-by-step, add board actions
    if (/formula|equation|x²|=|theorem/i.test(answer)) {
        if (!mixed.includes('pointBoard')) mixed.push('pointBoard');
        if (/step|first|second|third|then|next/i.test(answer) && !mixed.includes('writeBoard')) {
            mixed.push('writeBoard');
        }
    }

    // 4. Finalize
    if (mixed[mixed.length - 1] !== 'explaining') mixed.push('explaining');

    return [...seq, ...mixed];
}

// ─── Code syntax highlighting (simple keyword-based) ──────────────
const SYNTAX_RULES = {
    python: { keywords: ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif', 'for', 'while', 'in', 'not', 'and', 'or', 'try', 'except', 'finally', 'with', 'as', 'yield', 'lambda', 'pass', 'break', 'continue', 'True', 'False', 'None', 'print', 'raise', 'async', 'await'], comment: '#' },
    javascript: { keywords: ['function', 'const', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'class', 'import', 'from', 'export', 'default', 'new', 'this', 'async', 'await', 'try', 'catch', 'throw', 'true', 'false', 'null', 'undefined', 'console', 'typeof', 'switch', 'case'], comment: '//' },
    typescript: { keywords: ['function', 'const', 'let', 'var', 'return', 'if', 'else', 'for', 'while', 'class', 'import', 'from', 'export', 'default', 'new', 'this', 'async', 'await', 'try', 'catch', 'throw', 'true', 'false', 'null', 'undefined', 'console', 'typeof', 'interface', 'type', 'enum', 'switch', 'case'], comment: '//' },
    java: { keywords: ['public', 'private', 'protected', 'class', 'interface', 'extends', 'implements', 'return', 'if', 'else', 'for', 'while', 'new', 'this', 'static', 'void', 'int', 'String', 'boolean', 'try', 'catch', 'throw', 'final', 'abstract', 'import', 'package', 'true', 'false', 'null', 'System'], comment: '//' },
    cpp: { keywords: ['#include', 'int', 'void', 'return', 'if', 'else', 'for', 'while', 'class', 'public', 'private', 'protected', 'new', 'delete', 'using', 'namespace', 'std', 'cout', 'cin', 'endl', 'true', 'false', 'nullptr', 'template', 'virtual', 'const', 'auto', 'struct'], comment: '//' },
    c: { keywords: ['#include', 'int', 'void', 'return', 'if', 'else', 'for', 'while', 'struct', 'printf', 'scanf', 'char', 'float', 'double', 'long', 'short', 'unsigned', 'const', 'static', 'sizeof', 'NULL', 'typedef', 'enum'], comment: '//' },
    csharp: { keywords: ['using', 'namespace', 'class', 'public', 'private', 'protected', 'static', 'void', 'int', 'string', 'bool', 'return', 'if', 'else', 'for', 'while', 'new', 'this', 'var', 'async', 'await', 'try', 'catch', 'throw', 'true', 'false', 'null', 'Console'], comment: '//' },
    rust: { keywords: ['fn', 'let', 'mut', 'struct', 'impl', 'pub', 'use', 'mod', 'return', 'if', 'else', 'for', 'while', 'loop', 'match', 'true', 'false', 'self', 'Self', 'String', 'Vec', 'Option', 'Result', 'Some', 'None', 'Ok', 'Err', 'println', 'macro_rules'], comment: '//' },
    go: { keywords: ['func', 'package', 'import', 'return', 'if', 'else', 'for', 'range', 'var', 'const', 'type', 'struct', 'interface', 'map', 'chan', 'go', 'defer', 'select', 'true', 'false', 'nil', 'fmt', 'Println', 'err', 'error'], comment: '//' },
    ruby: { keywords: ['def', 'end', 'class', 'module', 'require', 'return', 'if', 'else', 'elsif', 'unless', 'while', 'do', 'puts', 'attr_accessor', 'include', 'true', 'false', 'nil', 'self', 'yield', 'block', 'proc', 'lambda'], comment: '#' },
    php: { keywords: ['function', 'class', 'public', 'private', 'protected', 'return', 'if', 'else', 'elseif', 'for', 'foreach', 'while', 'echo', 'print', 'new', 'this', 'true', 'false', 'null', 'use', 'namespace', 'require', 'include', 'array', '$'], comment: '//' },
    sql: { keywords: ['SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'ON', 'AND', 'OR', 'NOT', 'NULL', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'AS', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'INDEX', 'PRIMARY', 'KEY', 'FOREIGN'], comment: '--' },
    kotlin: { keywords: ['fun', 'val', 'var', 'class', 'object', 'interface', 'return', 'if', 'else', 'for', 'while', 'when', 'in', 'is', 'as', 'null', 'true', 'false', 'this', 'super', 'import', 'package', 'data', 'sealed', 'companion', 'override', 'suspend', 'println'], comment: '//' },
    swift: { keywords: ['func', 'var', 'let', 'class', 'struct', 'enum', 'protocol', 'return', 'if', 'else', 'for', 'while', 'switch', 'case', 'import', 'true', 'false', 'nil', 'self', 'Self', 'guard', 'print', 'throws', 'try', 'catch', 'async', 'await', 'some', 'any'], comment: '//' },
    html: { keywords: ['html', 'head', 'body', 'div', 'span', 'p', 'a', 'img', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'form', 'input', 'button', 'script', 'style', 'link', 'meta', 'title', 'class', 'id', 'src', 'href', 'type'], comment: '<!--' },
    css: { keywords: ['color', 'background', 'margin', 'padding', 'border', 'display', 'flex', 'grid', 'position', 'width', 'height', 'font', 'text', 'align', 'justify', 'content', 'items', 'center', 'none', 'block', 'inline', 'relative', 'absolute', 'fixed', 'z-index', 'opacity', 'transform', 'transition', 'animation', 'hover', 'media'], comment: '/*' },
    r: { keywords: ['function', 'if', 'else', 'for', 'while', 'return', 'library', 'require', 'TRUE', 'FALSE', 'NULL', 'NA', 'c', 'print', 'paste', 'data\.frame', 'matrix', 'list', 'vector', 'plot', 'ggplot', 'summary', 'mean', 'sd', 'var', 'length', 'nrow', 'ncol', 'read\.csv', 'write\.csv'], comment: '#' },
    scala: { keywords: ['def', 'val', 'var', 'class', 'object', 'trait', 'extends', 'with', 'import', 'return', 'if', 'else', 'for', 'while', 'match', 'case', 'true', 'false', 'null', 'this', 'super', 'new', 'override', 'abstract', 'sealed', 'yield', 'println', 'type', 'implicit', 'lazy'], comment: '//' },
};

function highlightSyntax(code, language) {
    const rules = SYNTAX_RULES[language] || SYNTAX_RULES['python'];
    const kwSet = new Set(rules.keywords);
    const lines = code.split('\n');

    function escHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    return lines.map(line => {
        // Split comment
        const commentIdx = (rules.comment !== '<!--' && rules.comment !== '/*')
            ? line.indexOf(rules.comment) : -1;
        const codePart = commentIdx >= 0 ? line.substring(0, commentIdx) : line;
        const commentPart = commentIdx >= 0 ? line.substring(commentIdx) : '';

        // Tokenize codePart into: strings, numbers, keywords, other
        const tokens = [];
        // Regex to split into: quoted strings, words/numbers, and everything else
        const tokenRegex = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\b\d+\.?\d*\b)|(\b[A-Za-z_#$][\w.]*\b)|([^"'`\w]+)/g;
        let m;
        while ((m = tokenRegex.exec(codePart)) !== null) {
            if (m[1]) { // string
                tokens.push(`<span class="syn-str">${escHtml(m[1])}</span>`);
            } else if (m[2]) { // number
                tokens.push(`<span class="syn-num">${escHtml(m[2])}</span>`);
            } else if (m[3]) { // word — check if keyword
                if (kwSet.has(m[3])) {
                    tokens.push(`<span class="syn-kw">${escHtml(m[3])}</span>`);
                } else {
                    tokens.push(escHtml(m[3]));
                }
            } else if (m[4]) { // other (operators, spaces, etc.)
                tokens.push(escHtml(m[4]));
            }
        }

        const codeHtml = tokens.join('');
        const commentHtml = commentPart
            ? `<span class="syn-cmt">${escHtml(commentPart)}</span>` : '';
        return codeHtml + commentHtml;
    });
}

function CodeBlockCard({ block }) {
    const [copied, setCopied] = useState(false);
    const lang = (block.language || 'code').toLowerCase();
    const title = block.title || `${lang} code`;
    const highlighted = highlightSyntax(block.code || '', lang);

    const handleCopy = () => {
        navigator.clipboard.writeText(block.code || '').then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    };

    return (
        <div className="code-syntax-block">
            <div className="csb-header">
                <span className="csb-lang-badge">{lang}</span>
                <span className="csb-title">{title}</span>
                <button className="csb-copy-btn" onClick={handleCopy}>
                    {copied ? '✓ Copied' : '📋 Copy'}
                </button>
            </div>
            <div className="csb-body">
                {highlighted.map((html, i) => (
                    <div key={i} className="csb-line">
                        <span className="csb-ln">{String(i + 1).padStart(3, ' ')}</span>
                        <span dangerouslySetInnerHTML={{ __html: html }} />
                    </div>
                ))}
            </div>
        </div>
    );
}

// ─── Single past chat message (no typewriter) ────────────────────
function ChatMessage({ entry }) {
    return (
        <div className="chat-msg-group">
            {/* User question bubble */}
            <div className="chat-bubble chat-user">
                <span className="chat-bubble-icon">🧑‍🎓</span>
                <span className="chat-bubble-text">{entry.q}</span>
            </div>
            {/* Teacher answer */}
            <div className="chat-bubble chat-teacher">
                <span className="chat-bubble-icon">👨‍🏫</span>
                <div className="chat-bubble-text">
                    {entry.diagram && (
                        <div className="tb-diagram-area" style={{ marginBottom: 10 }}>
                            <MermaidDiagram chart={entry.diagram} />
                        </div>
                    )}
                    {entry.image && (
                        <div style={{ margin: '8px 0', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(99,179,237,0.3)' }}>
                            <img src={`data:image/png;base64,${entry.image}`} alt="AI visual" style={{ width: '100%', maxHeight: 250, objectFit: 'contain', display: 'block', background: 'rgba(10,15,40,0.4)' }} />
                        </div>
                    )}
                    <span style={{ whiteSpace: 'pre-wrap' }}>{entry.a}</span>
                    {entry.codeBlocks && entry.codeBlocks.length > 0 && (
                        <div className="tb-code-blocks" style={{ marginTop: 10 }}>
                            {entry.codeBlocks.map((block, i) => (
                                <CodeBlockCard key={i} block={block} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ─── Classroom Board showing chat-style Q&A ───────────────────────
function ClassroomBoard({ chatHistory, question, answer, diagram, codeBlocks, apiImage, animState, isLoading }) {
    const [displayedText, setDisplayedText] = useState('');
    const [isWriting, setIsWriting] = useState(false);
    const boardEndRef = useRef(null);

    useEffect(() => {
        setDisplayedText('');
        if (!answer) return;
        let current = '';
        let i = 0;
        setIsWriting(true);
        const iv = setInterval(() => {
            current += answer[i];
            setDisplayedText(current);
            i++;
            if (i >= answer.length) { clearInterval(iv); setIsWriting(false); }
        }, 15);
        return () => clearInterval(iv);
    }, [answer]);

    // Auto-scroll to bottom on new content
    useEffect(() => {
        boardEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chatHistory.length, displayedText.length > 0]);

    const hasContent = chatHistory.length > 0 || answer || isLoading;

    return (
        <div className={`teacher-board tb-${animState}`}>
            {/* Header */}
            <div className="tb-header">
                <div className="tb-chalk-tray" />
                <span className="tb-title">
                    {isLoading ? '💭 Thinking…' : '📋 Classroom Board'}
                </span>
            </div>

            {/* Board surface — scrollable chat thread */}
            <div className="tb-surface" style={{ overflowY: 'auto', maxHeight: '70vh' }}>
                {!hasContent ? (
                    <div className="tb-empty">
                        <span className="tb-empty-icon">📘</span>
                        <span className="tb-empty-text">Ask me anything…</span>
                    </div>
                ) : (
                    <div className="tb-content tb-chat-thread">
                        {/* Past conversation messages */}
                        {chatHistory.map((entry, i) => (
                            <ChatMessage key={entry.id || i} entry={entry} />
                        ))}

                        {/* Current active question + answer (with typewriter) */}
                        {(question && (answer || isLoading)) && (
                            <div className="chat-msg-group chat-msg-active">
                                <div className="chat-bubble chat-user">
                                    <span className="chat-bubble-icon">🧑‍🎓</span>
                                    <span className="chat-bubble-text">{question}</span>
                                </div>

                                {isLoading ? (
                                    <div className="chat-bubble chat-teacher">
                                        <span className="chat-bubble-icon">👨‍🏫</span>
                                        <div className="tb-loading" style={{ padding: '8px 0' }}>
                                            <div className="tb-think-dots"><span /><span /><span /></div>
                                            <span className="tb-think-label">Preparing answer…</span>
                                        </div>
                                    </div>
                                ) : answer && (
                                    <div className="chat-bubble chat-teacher">
                                        <span className="chat-bubble-icon">👨‍🏫</span>
                                        <div className="chat-bubble-text">
                                            {diagram && (
                                                <div className="tb-diagram-area" style={{ marginBottom: 10 }}>
                                                    <MermaidDiagram chart={diagram} />
                                                </div>
                                            )}
                                            {apiImage && (
                                                <div style={{ margin: '10px 0', borderRadius: 10, overflow: 'hidden', border: '2px solid rgba(99,179,237,0.4)', position: 'relative' }}>
                                                    <img src={`data:image/png;base64,${apiImage}`} alt="AI visual" style={{ width: '100%', maxHeight: 350, objectFit: 'contain', display: 'block', background: 'rgba(10,15,40,0.5)' }} />
                                                    <div style={{ position: 'absolute', bottom: 6, right: 8, background: 'rgba(0,0,0,0.6)', color: '#63b3ed', fontSize: 10, padding: '2px 8px', borderRadius: 6, fontWeight: 600 }}>🎨 AI Generated</div>
                                                </div>
                                            )}
                                            <div className="tb-text-area" style={{ whiteSpace: 'pre-wrap' }}>
                                                <span className="tb-chalk-text">
                                                    {displayedText}
                                                    {animState === 'writeBoard' && isWriting && <span className="tb-inline-pencil">✏️</span>}
                                                </span>
                                            </div>
                                            {codeBlocks && codeBlocks.length > 0 && (
                                                <div className="tb-code-blocks" style={{ marginTop: 10 }}>
                                                    {codeBlocks.map((block, i) => <CodeBlockCard key={i} block={block} />)}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        <div ref={boardEndRef} />
                    </div>
                )}

                {(animState === 'pointBoard') && answer && (
                    <div className="tb-pointer"><span className="tb-pointer-arrow">➜</span></div>
                )}
            </div>
            <div className="tb-chalk-dust" />
        </div>
    );
}

// ─── Simple question input bar (with file upload) ─────────────────
function QuestionInput({ onAsk, isLoading }) {
    const [text, setText] = useState('');
    const [voiceOn, setVoiceOn] = useState(false);
    const [attachedFile, setAttachedFile] = useState(null);   // { file, name }
    const [fileError, setFileError] = useState('');
    const recogRef = useRef(null);
    const fileInputRef = useRef(null);

    const ACCEPTED = '.txt,.md,.csv,.pdf,.docx,.png,.jpg,.jpeg,.webp';

    const handleFileChange = (e) => {
        const f = e.target.files?.[0];
        if (!f) return;
        const maxMB = 10;
        if (f.size > maxMB * 1024 * 1024) {
            setFileError(`File too large (max ${maxMB} MB)`);
            return;
        }
        setFileError('');
        setAttachedFile({ file: f, name: f.name });
        // Reset native input so same file can be re-selected
        e.target.value = '';
    };

    const removeFile = () => {
        setAttachedFile(null);
        setFileError('');
    };

    const submit = () => {
        const t = text.trim();
        if (!t || isLoading) return;
        onAsk(t, attachedFile?.file || null);
        setText('');
        setAttachedFile(null);
        setFileError('');
    };

    const startVoice = () => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { alert('Voice input requires Chrome or Edge.'); return; }
        const r = new SR();
        r.lang = 'en-US';
        r.interimResults = true;
        r.onresult = e => setText(Array.from(e.results).map(x => x[0].transcript).join(''));
        r.onend = () => setVoiceOn(false);
        r.onerror = () => setVoiceOn(false);
        r.start();
        recogRef.current = r;
        setVoiceOn(true);
    };
    const stopVoice = () => { recogRef.current?.stop(); setVoiceOn(false); };

    // File type → emoji
    const fileIcon = (name) => {
        const ext = name.split('.').pop().toLowerCase();
        if (ext === 'pdf') return '📄';
        if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) return '🖼️';
        if (ext === 'docx') return '📝';
        return '📎';
    };

    return (
        <div className="tqi-wrap">
            {/* File chip */}
            {attachedFile && (
                <div className="tqi-file-chip">
                    <span className="tqi-file-icon">{fileIcon(attachedFile.name)}</span>
                    <span className="tqi-file-name">{attachedFile.name}</span>
                    <button className="tqi-file-remove" onClick={removeFile} title="Remove file">✕</button>
                </div>
            )}
            {fileError && <div className="tqi-file-error">⚠️ {fileError}</div>}

            <div className={`tqi-inner ${voiceOn ? 'tqi-listening' : ''} ${attachedFile ? 'tqi-has-file' : ''}`}>
                <span className="tqi-icon">🎓</span>
                <input
                    className="tqi-input"
                    placeholder={isLoading
                        ? 'Explaining…'
                        : voiceOn
                            ? '🎤 Listening — speak your question'
                            : attachedFile
                                ? `Ask something about "${attachedFile.name}"…`
                                : 'Ask the teacher anything… or 📎 attach a file'}
                    value={text}
                    onChange={e => setText(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && submit()}
                    disabled={isLoading}
                />

                {/* Hidden file input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED}
                    style={{ display: 'none' }}
                    onChange={handleFileChange}
                />

                {/* Paperclip button */}
                <button
                    className={`tqi-attach ${attachedFile ? 'tqi-attach-active' : ''}`}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    title="Attach a file (txt, pdf, docx, image)"
                >
                    📎
                </button>

                <button
                    className={`tqi-mic ${voiceOn ? 'tqi-mic-on' : ''}`}
                    onClick={voiceOn ? stopVoice : startVoice}
                    disabled={isLoading}
                    title="Speak your question"
                >
                    {voiceOn ? <span className="tqi-waves"><span /><span /><span /></span> : '🎤'}
                </button>
                <button
                    className="tqi-ask"
                    onClick={submit}
                    disabled={!text.trim() || isLoading}
                >
                    {isLoading ? <span className="tqi-spinner" /> : '➤ Ask'}
                </button>
            </div>
            {voiceOn && (
                <div className="tqi-voice-hint">
                    <div className="tqi-vbars">
                        {[...Array(10)].map((_, i) => (
                            <span key={i} style={{ animationDelay: `${i * 0.09}s` }} />
                        ))}
                    </div>
                    <span>Listening… speak now</span>
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────
//  TEACHER PAGE
// ─────────────────────────────────────────────────────────────────
export default function TeacherPage() {
    const [animState, setAnimState] = useState('idle');
    const [animLabel, setAnimLabel] = useState('');
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [topic, setTopic] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [currentViseme, setCurrentViseme] = useState('viseme_sil');
    const [avatarPos, setAvatarPos] = useState({ x: 80, y: 70 });
    const [qaHistory, setQaHistory] = useState(() => {
        try { return JSON.parse(localStorage.getItem('ai_teacher_library') || '[]'); }
        catch { return []; }
    });
    const [showLibrary, setShowLibrary] = useState(false);
    const [diagram, setDiagram] = useState(null);
    const [visualScene, setVisualScene] = useState('');
    const [spokenTextForVision, setSpokenTextForVision] = useState('');
    const [visionTrigger, setVisionTrigger] = useState(0);
    const skillLevel = 'advanced'; // locked to advanced — mode switcher removed
    const [showQuiz, setShowQuiz] = useState(false);
    const [showTopics, setShowTopics] = useState(false);
    const [selectedTopic, setSelectedTopic] = useState('');
    const [imageRequested, setImageRequested] = useState(false);
    const [apiVideo, setApiVideo] = useState('');
    const [apiImage, setApiImage] = useState('');
    const [rekLabels, setRekLabels] = useState([]);
    const [codeBlocks, setCodeBlocks] = useState([]);
    const [chatHistory, setChatHistory] = useState([]);

    const visionRef = useRef(null);

    const seqTimersRef = useRef([]);
    const audioSrcRef = useRef(null);
    const visTimersRef = useRef([]);

    // ── Clear all timers ────────────────────────────────────────────
    const clearAll = () => {
        seqTimersRef.current.forEach(clearTimeout);
        seqTimersRef.current = [];
        visTimersRef.current.forEach(clearTimeout);
        visTimersRef.current = [];
        try { audioSrcRef.current?.stop(); } catch { }
        window.speechSynthesis?.cancel();
        setIsSpeaking(false);
    };

    // ── Browser TTS fallback ────────────────────────────────────────
    const speakFallback = useCallback((text) => {
        if (!text || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.rate = 0.92;
        utter.pitch = 1.05;
        const voices = window.speechSynthesis.getVoices();
        const pick = voices.find(v => v.name.includes('Google UK English Male'))
            || voices.find(v => v.lang.startsWith('en')) || voices[0];
        if (pick) utter.voice = pick;

        utter.onstart = () => {
            setIsSpeaking(true);
            setCurrentViseme('viseme_sil');
        };
        utter.onboundary = (e) => {
            if (e.name === 'word') {
                const word = text.substr(e.charIndex, e.charLength || 4);
                const v = wordToViseme(word);
                setCurrentViseme(v);
                setTimeout(() => setCurrentViseme('viseme_sil'), Math.max(120, (e.charLength || 4) * 55));
            }
        };
        utter.onend = () => { setIsSpeaking(false); setCurrentViseme('viseme_sil'); };
        utter.onerror = () => { setIsSpeaking(false); setCurrentViseme('viseme_sil'); };
        window.speechSynthesis.speak(utter);
    }, []);

    // ── Schedule visemes from Polly marks ───────────────────────────
    const scheduleVisemes = useCallback((speechMarks) => {
        visTimersRef.current.forEach(clearTimeout);
        visTimersRef.current = [];
        const marks = speechMarks.filter(m => m.type === 'viseme');
        marks.forEach(mark => {
            const t = setTimeout(() => {
                setCurrentViseme(mark.viseme_key || 'viseme_aa');
                const silTimer = setTimeout(() => setCurrentViseme('viseme_sil'), 80);
                visTimersRef.current.push(silTimer);
            }, mark.time_ms);
            visTimersRef.current.push(t);
        });
        const lastTime = marks.length ? marks[marks.length - 1].time_ms + 200 : 0;
        const endTimer = setTimeout(() => {
            setCurrentViseme('viseme_sil');
            setIsSpeaking(false);
        }, lastTime);
        visTimersRef.current.push(endTimer);
    }, []);

    // ── Play Polly audio or fallback ───────────────────────────────
    const speak = useCallback(async (data) => {
        if (data.audio_base64) {
            try {
                setIsSpeaking(true);
                setCurrentViseme('viseme_sil');
                if (data.speech_marks) scheduleVisemes(data.speech_marks);
                audioSrcRef.current = await decodeAndPlay(data.audio_base64, () => {
                    setIsSpeaking(false);
                    setCurrentViseme('viseme_sil');
                });
                return;
            } catch { }
        }
        speakFallback(data.spoken_text || data.explanation || '');
    }, [speakFallback, scheduleVisemes]);

    // ── Play animation sequence driven by content ───────────────────
    const playSequence = useCallback((states, questionText, answerText) => {
        clearAll();
        if (!states.length) return;
        // First state immediately
        setAnimState(states[0]);

        // Queue subsequent states with delays
        states.slice(1).forEach((s, i) => {
            const t = setTimeout(() => {
                setAnimState(s);
                // Move towards board when pointing or writing
                if (s === 'pointBoard' || s === 'writeBoard') {
                    setAvatarPos({ x: 35, y: 55 }); // Near the board
                } else if (s === 'smile' || s === 'explaining') {
                    setAvatarPos({ x: 80, y: 70 }); // Default explaining pos
                }
            }, (i + 1) * 2400);
            seqTimersRef.current.push(t);
        });

        // Return to explaining after sequence, then idle
        const totalDur = states.length * 2400;
        const t1 = setTimeout(() => { setAnimState('explaining'); }, totalDur);
        const t2 = setTimeout(() => {
            setAnimState('idle');
            setAvatarPos({ x: 85, y: 75 }); // Idle corner
        }, totalDur + 4000);
        seqTimersRef.current.push(t1, t2);
    }, []);

    // ── Detect if the user is asking for an image ───────────────────
    const detectsImageRequest = (q) =>
        /\b(show|give|generate|create|draw|display|make|produce|render|visuali[sz]e|image|picture|photo|illustration|diagram|sketch|depict|what does .* look like|how does .* look)\b/i.test(q);

    // ── Main Q&A handler ────────────────────────────────────────────
    const handleAsk = useCallback(async (q, file = null) => {
        clearAll();
        // Push previous Q&A into chat history before starting new one
        if (question && answer) {
            setChatHistory(prev => [...prev, {
                id: Date.now(),
                q: question,
                a: answer,
                diagram: diagram,
                image: apiImage,
                codeBlocks: codeBlocks,
            }]);
        }
        setQuestion(q);
        setAnswer('');
        setIsLoading(true);
        const askedForImage = detectsImageRequest(q);
        setImageRequested(askedForImage);

        // While loading → nod (teacher acknowledging)
        setAnimState('nod');

        try {
            // Prepend selected topic context to the question for topic-aware answers
            const contextQ = selectedTopic
                ? `[Topic: ${selectedTopic}] ${q}`
                : q;
            const data = file
                ? await askQuestionWithFile(contextQ, skillLevel, SESSION_ID, file)
                : await askQuestion(contextQ, skillLevel, SESSION_ID);
            const ans = data.explanation || data.spoken_text || '';
            const topicName = data.topic || q.slice(0, 40);

            // Extract mermaid diagram if present in explanation
            const mermaidMatch = ans.match(/```mermaid([\s\S]*?)```/);
            const diagramFromExplanation = mermaidMatch ? mermaidMatch[1].trim() : null;

            // Fall back to the dedicated flow_diagram field if explanation had no block
            const diagramFound = diagramFromExplanation || data.flow_diagram || null;

            // Clean the text: remove the mermaid block so it doesn't type out raw code
            const cleanText = ans.replace(/```mermaid[\s\S]*?```/g, '').trim();

            setDiagram(diagramFound);
            setAnswer(cleanText);
            setTopic(topicName);
            setIsLoading(false);

            // Store API video and Rekognition labels from response
            setApiVideo(data.video_b64 || '');
            setApiImage(data.image_b64 || '');
            setRekLabels(data.rekognition_labels || []);
            setCodeBlocks(data.code_blocks || []);

            // Trigger AI image generation
            // If user explicitly asked for an image → use the question directly as prompt
            // Otherwise → use the AI-generated visual_scene description
            const imagePrompt = askedForImage
                ? q                                          // e.g. "Show me a diagram of photosynthesis"
                : (data.visual_scene || cleanText.slice(0, 200));

            const spoken = data.spoken_text || cleanText;
            setVisualScene(imagePrompt);
            setSpokenTextForVision(spoken);

            // Only trigger the image panel when user explicitly asked for an image
            if (askedForImage) {
                setVisionTrigger(v => v + 1);
                setTimeout(() => {
                    visionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 800);
            }

            // Add to library (persisted in localStorage)
            const newEntry = {
                id: Date.now(),
                q,
                a: ans,
                topic: topicName,
                diagram: diagramFound || null,
                time: new Date().toLocaleString(),
            };
            setQaHistory(prev => {
                const updated = [newEntry, ...prev].slice(0, 30);
                try { localStorage.setItem('ai_teacher_library', JSON.stringify(updated)); } catch { }
                return updated;
            });

            // Build content-driven animation sequence
            const seq = buildAnimSequence(q, ans);
            playSequence(seq, q, ans);

            // Speak the answer
            await speak(data);

        } catch (err) {
            const fallbackAns = '⚠️ Could not connect to the AI teacher. Please make sure the backend is running.';
            setAnswer(fallbackAns);
            setIsLoading(false);
            setAnimState('serious');
            setTimeout(() => setAnimState('idle'), 2500);
        }
    }, [playSequence, speak, skillLevel]);

    // Cleanup on unmount
    useEffect(() => () => clearAll(), []);

    return (
        <div className="teacher-page" style={{ position: 'relative', overflowY: 'auto', minHeight: '100vh', width: '100vw' }}>

            {/* 3D Avatar - Floating absolutely */}
            <div className="tc-floating-avatar" style={{
                position: 'fixed',
                left: `${avatarPos.x}%`,
                top: `${avatarPos.y}%`,
                width: '320px',
                height: '420px',
                zIndex: 100,
                transform: 'translate(-50%, -50%)',
                transition: 'all 2.4s cubic-bezier(0.19, 1, 0.22, 1)',
                pointerEvents: 'none'
            }}>
                <Avatar
                    agentState={animState}
                    isSpeaking={isSpeaking}
                    currentViseme={currentViseme}
                />
            </div>

            {/* ── Top-right action buttons ── */}
            <div style={{ position: 'fixed', top: '68px', right: '20px', zIndex: 9000, display: 'flex', gap: '10px', alignItems: 'center' }}>
                {/* Library button — always visible */}
                <button
                    onClick={() => setShowLibrary(v => !v)}
                    style={{
                        padding: '8px 18px',
                        borderRadius: '20px',
                        border: `1px solid ${showLibrary ? 'rgba(139,92,246,0.8)' : 'rgba(139,92,246,0.35)'}`,
                        background: showLibrary
                            ? 'linear-gradient(135deg,rgba(109,40,217,0.7),rgba(139,92,246,0.5))'
                            : 'linear-gradient(135deg,rgba(109,40,217,0.35),rgba(139,92,246,0.2))',
                        color: '#c4b5fd',
                        fontWeight: 600,
                        fontSize: '13px',
                        cursor: 'pointer',
                        backdropFilter: 'blur(10px)',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                    }}
                >
                    📚 Library {qaHistory.length > 0 && <span style={{ background: 'rgba(167,139,250,0.3)', borderRadius: '50px', padding: '1px 7px', fontSize: '11px' }}>{qaHistory.length}</span>}
                </button>

                {/* Quiz button — only after an answer */}
                {topic && (
                    <button
                        onClick={() => setShowQuiz(true)}
                        style={{
                            padding: '8px 20px',
                            borderRadius: '20px',
                            border: '1px solid rgba(52,211,153,0.4)',
                            background: 'linear-gradient(135deg,rgba(5,150,105,0.6),rgba(4,120,87,0.4))',
                            color: '#6ee7b7',
                            fontWeight: 600,
                            fontSize: '13px',
                            cursor: 'pointer',
                            backdropFilter: 'blur(10px)',
                            transition: 'all 0.2s',
                        }}
                    >
                        📝 Quiz on "{topic.slice(0, 24)}{topic.length > 24 ? '…' : ''}"
                    </button>
                )}
            </div>

            {/* ── Classroom area ─── */}
            <div className="teacher-classroom" style={{ display: 'block', padding: '40px', paddingTop: '80px', paddingBottom: '120px' }}>
                <div className="tc-board-container" style={{ maxWidth: '900px', margin: '0 auto' }}>
                    <ClassroomBoard
                        chatHistory={chatHistory}
                        question={question}
                        answer={answer.replace(/```mermaid[\s\S]*?```/g, '')}
                        diagram={diagram}
                        codeBlocks={codeBlocks}
                        apiImage={apiImage}
                        animState={animState}
                        isLoading={isLoading}
                    />
                </div>

                {/* AI Vision Panel — shown when image requested OR when AWS data (video/Rekognition) is available */}
                {(imageRequested || apiVideo || rekLabels.length > 0) && (
                    <div
                        ref={visionRef}
                        className="tc-vision-wrap"
                        style={{
                            border: '2px solid rgba(99,179,237,0.6)',
                            borderRadius: '16px',
                            boxShadow: '0 0 32px rgba(99,179,237,0.25)',
                            padding: '4px',
                            background: 'rgba(10,20,50,0.4)',
                            transition: 'all 0.5s ease',
                            marginTop: '24px',
                        }}
                    >
                        {/* 🖼 Image-requested banner */}
                        {visionTrigger > 0 && (
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                background: 'linear-gradient(90deg, rgba(59,130,246,0.15), rgba(99,179,237,0.08))',
                                borderBottom: '1px solid rgba(99,179,237,0.2)',
                                borderRadius: '14px 14px 0 0',
                                fontSize: '13px',
                                color: '#93c5fd',
                                fontWeight: 600,
                                letterSpacing: '0.03em',
                            }}>
                                <span style={{ fontSize: '16px' }}>🖼</span>
                                Image generated for: <em style={{ color: '#bfdbfe', fontStyle: 'normal' }}>"{question.slice(0, 60)}{question.length > 60 ? '…' : ''}"</em>
                            </div>
                        )}
                        <VisionPanel
                            visualScene={visualScene}
                            topic={question}
                            spokenText={spokenTextForVision}
                            trigger={visionTrigger}
                            apiVideo={apiVideo}
                            rekLabels={rekLabels}
                        />
                    </div>
                )}

                {/* ── Q&A Library drawer (slide-in from left) ─── */}
                {showLibrary && (
                    <div className="lib-overlay" style={{ zIndex: 9001 }} onClick={() => setShowLibrary(false)}>
                        <div className="lib-drawer" onClick={e => e.stopPropagation()}>
                            <div className="lib-header">
                                <span className="lib-title">📚 Library</span>
                                <span className="lib-count">{qaHistory.length} saved</span>
                                {qaHistory.length > 0 && (
                                    <button className="lib-clear" onClick={() => {
                                        if (confirm('Clear all saved questions?')) {
                                            setQaHistory([]);
                                            try { localStorage.removeItem('ai_teacher_library'); } catch { }
                                        }
                                    }}>🗑 Clear</button>
                                )}
                                <button className="lib-close" onClick={() => setShowLibrary(false)}>✕</button>
                            </div>

                            {qaHistory.length === 0 ? (
                                <div className="lib-empty">
                                    <span className="lib-empty-icon">📖</span>
                                    <p>No questions yet.<br />Ask something to start your library!</p>
                                </div>
                            ) : (
                                <div className="lib-list">
                                    {qaHistory.map((h) => (
                                        <div key={h.id} className="lib-item" style={{ position: 'relative' }} onClick={() => {
                                            setAnswer('');
                                            setQuestion(h.q);
                                            setTopic(h.topic || '');
                                            setDiagram(h.diagram || null);
                                            setTimeout(() => {
                                                setAnswer(h.a);
                                                setAnimState('explaining');
                                            }, 30);
                                            setShowLibrary(false);
                                        }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div className="lib-item-topic">{h.topic || '📋 Question'}</div>
                                                    <div className="lib-item-q">{h.q}</div>
                                                </div>
                                                <button
                                                    title="Delete this item"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        const updated = qaHistory.filter(item => item.id !== h.id);
                                                        setQaHistory(updated);
                                                        try { localStorage.setItem('ai_teacher_library', JSON.stringify(updated)); } catch { }
                                                    }}
                                                    style={{
                                                        background: 'rgba(239,68,68,0.15)',
                                                        border: '1px solid rgba(239,68,68,0.3)',
                                                        borderRadius: '6px',
                                                        color: '#f87171',
                                                        cursor: 'pointer',
                                                        padding: '4px 8px',
                                                        fontSize: '13px',
                                                        flexShrink: 0,
                                                        marginLeft: '8px',
                                                        transition: 'all 0.2s',
                                                    }}
                                                    onMouseEnter={e => { e.target.style.background = 'rgba(239,68,68,0.35)'; e.target.style.color = '#fca5a5'; }}
                                                    onMouseLeave={e => { e.target.style.background = 'rgba(239,68,68,0.15)'; e.target.style.color = '#f87171'; }}
                                                >🗑</button>
                                            </div>
                                            <div className="lib-item-time">{h.time}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

            </div>

            {/* ── Question input bar — sticky at bottom ─── */}
            <div style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                zIndex: 300,
                background: 'rgba(8,4,24,0.92)',
                backdropFilter: 'blur(20px)',
                borderTop: '1px solid rgba(120,80,255,0.2)',
                padding: '10px 20px 14px',
            }}>
                {/* Topic Browser — toggled above input */}
                {showTopics && (
                    <div className="topic-browser" style={{ maxHeight: '200px', overflowY: 'auto', marginBottom: '8px' }}>
                        <div className="topic-browser-header">
                            <span className="topic-browser-label">📚 Select a Topic</span>
                            <button className="topic-browser-close" onClick={() => setShowTopics(false)}>✕</button>
                        </div>
                        {[
                            { cat: '💻 Programming', items: ['Python Basics', 'JavaScript Functions', 'Java OOP', 'C++ Pointers', 'Rust Ownership', 'Go Concurrency', 'SQL Queries', 'TypeScript Types'] },
                            { cat: '🌐 Web Dev', items: ['React Hooks', 'CSS Flexbox & Grid', 'REST API Design', 'Node.js Express', 'HTML5 Semantic Elements'] },
                            { cat: '🧠 CS Fundamentals', items: ['Data Structures', 'Algorithms', 'Big O Notation', 'Binary Search', 'Sorting Algorithms', 'Dynamic Programming', 'OOP Principles'] },
                            { cat: '🤖 AI & ML', items: ['Machine Learning Basics', 'Neural Networks', 'Deep Learning', 'NLP', 'Computer Vision'] },
                            { cat: '🔧 System Design', items: ['Operating Systems', 'DBMS Basics', 'Microservices', 'Caching Strategies'] },
                        ].map(({ cat, items }) => (
                            <div key={cat}>
                                <div className="topic-cat-title">{cat}</div>
                                <div className="topic-grid">
                                    {items.map(t => (
                                        <button
                                            key={t}
                                            className={`topic-chip${selectedTopic === t ? ' topic-chip-active' : ''}`}
                                            onClick={() => {
                                                setSelectedTopic(t);
                                                setShowTopics(false);
                                            }}
                                        >{t}</button>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
                {/* Selected topic badge */}
                {selectedTopic && (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '8px',
                        marginBottom: '8px', padding: '6px 14px',
                        background: 'rgba(99,102,241,0.15)',
                        border: '1px solid rgba(99,102,241,0.4)',
                        borderRadius: '10px', width: 'fit-content',
                    }}>
                        <span style={{ color: '#a5b4fc', fontSize: '12px', fontWeight: 600, letterSpacing: '0.5px' }}>📌 TOPIC</span>
                        <span style={{ color: '#e0e7ff', fontSize: '14px', fontWeight: 500 }}>{selectedTopic}</span>
                        <button
                            onClick={() => setSelectedTopic('')}
                            style={{
                                background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)',
                                borderRadius: '6px', color: '#f87171', cursor: 'pointer',
                                padding: '2px 7px', fontSize: '12px', marginLeft: '4px',
                            }}
                            title="Clear topic"
                        >✕</button>
                    </div>
                )}
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                    <button
                        onClick={() => setShowTopics(v => !v)}
                        style={{
                            padding: '10px 14px',
                            borderRadius: '12px',
                            border: `1px solid ${showTopics ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.2)'}`,
                            background: showTopics ? 'rgba(99,102,241,0.2)' : 'rgba(99,102,241,0.08)',
                            color: '#a5b4fc',
                            cursor: 'pointer',
                            fontSize: '16px',
                            transition: 'all 0.2s',
                            flexShrink: 0,
                        }}
                        title="Browse Topics"
                    >📚</button>
                    <div style={{ flex: 1 }}>
                        <QuestionInput onAsk={handleAsk} isLoading={isLoading} />
                    </div>
                </div>
            </div>

            {/* ── Quiz modal ─── */}
            {showQuiz && (
                <Quiz
                    topic={topic}
                    skillLevel={skillLevel}
                    userId={SESSION_ID}
                    onClose={() => setShowQuiz(false)}
                />
            )}
        </div>
    );
}
