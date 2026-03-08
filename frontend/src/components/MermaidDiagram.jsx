import { useEffect, useRef, memo, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif',
    flowchart: { curve: 'basis', useMaxWidth: true },
    logLevel: 5, // silence mermaid internal logs
});

let _seq = 0;
const uid = () => `mmd${++_seq}`;

// ── Strip backtick fences the AI sometimes adds ─────────────────────────────
function stripFences(raw) {
    return raw
        .replace(/^```mermaid\s*/i, '')
        .replace(/^```\s*/i, '')
        .replace(/```\s*$/, '')
        .trim();
}

// ── Fix the most common syntax mistakes from AI-generated mermaid ────────────
function sanitize(code) {
    const VALID_TYPES = ['flowchart', 'graph', 'sequenceDiagram', 'classDiagram',
        'stateDiagram', 'pie', 'gantt', 'erDiagram', 'journey', 'gitGraph'];

    let lines = code.split('\n');

    // Ensure it starts with a valid diagram type keyword
    const first = lines.find(l => l.trim());
    if (!first || !VALID_TYPES.some(t => first.trim().toLowerCase().startsWith(t.toLowerCase()))) {
        lines.unshift('flowchart TD');
    }

    lines = lines.map(line => {
        // Quote node labels containing special characters: A[label (with) parens]
        line = line.replace(
            /(\b[\w]+)\[(?!")([^\]"]*[(){}|:<>\/\\+=@!?][^\]"]*)\]/g,
            (_, id, lbl) => `${id}["${lbl.replace(/"/g, "'")}"]`
        );
        // Quote round-bracket node labels with special chars: A(label: text)
        line = line.replace(
            /(\b[\w]+)\((?!")([^)"]*[{}|:<>\/\\+=@!?][^)"]*)\)(?!\))/g,
            (_, id, lbl) => `${id}("${lbl.replace(/"/g, "'")}")`
        );
        // Convert pipe edge labels |text| → -- "text" -->
        line = line.replace(/-->\s*\|([^|]+)\|/g, '-- "$1" -->');
        // Remove stray > inside quoted edge labels
        line = line.replace(/(--\s*"[^"]*?)>([^"]*?")/g, '$1$2');
        return line;
    });

    return lines.join('\n');
}

// ── CRITICAL: remove orphan elements mermaid v11 leaves in <body> on failure ─
function removeMermaidOrphans(id) {
    // mermaid v11 creates: <div id="d{id}"> in document.body on parse failure
    [`d${id}`, `mermaid-${id}`, id].forEach(eid => {
        const el = document.getElementById(eid);
        if (el) el.remove();
    });
    // Also sweep any lingering mermaid error divs injected into body
    document.querySelectorAll('[id^="dmmd"]').forEach(el => el.remove());
}

// ── Build a guaranteed-valid fallback from broken chart text ─────────────────
function buildFallback(raw) {
    const words = (raw.match(/\b[A-Z][a-z]{2,}\b/g) || []);
    const unique = [...new Set(words)].slice(0, 5);
    if (unique.length >= 2) {
        const nodes = unique.map((w, i) => `  N${i}["${w}"]`).join('\n');
        const arrows = unique.slice(1).map((_, i) => `  N${i} --> N${i + 1}`).join('\n');
        return `flowchart TD\n${nodes}\n${arrows}`;
    }
    return 'flowchart TD\n  A["Concept"] --> B["Explanation"] --> C["Application"]';
}

// ── Safe render: renders code, cleans up on failure, returns svg or throws ───
async function safeRender(code) {
    const id = uid();
    try {
        // First validate with parse so we never even get to the bad render
        await mermaid.parse(code);
        const { svg } = await mermaid.render(id, code);
        removeMermaidOrphans(id); // clean up even on success
        return svg;
    } catch (e) {
        removeMermaidOrphans(id); // MUST remove orphan error divs from body
        throw e;
    }
}

// ── Component ────────────────────────────────────────────────────────────────
const MermaidDiagram = memo(function MermaidDiagram({ chart }) {
    const ref = useRef(null);
    const [isFallback, setIsFallback] = useState(false);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        if (!chart || !ref.current) return;
        let cancelled = false;

        setIsFallback(false);
        setFailed(false);
        ref.current.innerHTML = '';

        const raw = stripFences(chart);

        (async () => {
            // Attempt 1 — sanitized version
            try {
                const svg = await safeRender(sanitize(raw));
                if (!cancelled && ref.current) { ref.current.innerHTML = svg; }
                return;
            } catch { /* continue */ }

            // Attempt 2 — raw original
            try {
                const svg = await safeRender(raw);
                if (!cancelled && ref.current) { ref.current.innerHTML = svg; }
                return;
            } catch { /* continue */ }

            // Attempt 3 — guaranteed fallback (always valid)
            try {
                const svg = await safeRender(buildFallback(raw));
                if (!cancelled && ref.current) {
                    ref.current.innerHTML = svg;
                    setIsFallback(true);
                }
            } catch {
                if (!cancelled) setFailed(true);
            }
        })();

        return () => { cancelled = true; };
    }, [chart]);

    if (!chart) return null;

    return (
        <div style={{
            background: 'rgba(0,0,0,0.2)',
            borderRadius: '12px',
            padding: '16px',
            margin: '10px 0',
            border: '1px solid rgba(129,140,248,0.2)',
            overflowX: 'auto',
        }}>
            {failed
                ? <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0, fontStyle: 'italic' }}>📊 Diagram unavailable</p>
                : <div ref={ref} />
            }
            {isFallback && !failed && (
                <p style={{ color: '#94a3b8', fontSize: '11px', margin: '4px 0 0', textAlign: 'right', fontStyle: 'italic' }}>✨ simplified diagram</p>
            )}
        </div>
    );
});

export default MermaidDiagram;
