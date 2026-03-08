import { useEffect, useRef, useState } from 'react';

/**
 * Whiteboard – shows text instantly with a smooth fade-in.
 * Removed the slow character-by-character typewriter that caused
 * a big gap between what you read and what the avatar says.
 */
export default function Whiteboard({ text, isLoading }) {
    const [displayText, setDisplayText] = useState('');
    const [fadeKey, setFadeKey] = useState(0);

    useEffect(() => {
        if (text) {
            setDisplayText(text);
            setFadeKey(k => k + 1);   // triggers CSS fade-in animation
        } else {
            setDisplayText('');
        }
    }, [text]);

    return (
        <div className="whiteboard">
            <div className="whiteboard-header">
                <span className="chalk-dot red" />
                <span className="chalk-dot yellow" />
                <span className="chalk-dot green" />
                <span className="whiteboard-title">📋 Explanation</span>
            </div>
            <div className="whiteboard-body">
                {isLoading ? (
                    <div className="loading-dots">
                        <span /><span /><span />
                    </div>
                ) : displayText ? (
                    <p
                        key={fadeKey}
                        className="chalk-text chalk-fade-in"
                    >
                        {displayText}
                    </p>
                ) : (
                    <p className="chalk-placeholder">
                        ✨ Ask me anything! I'll explain it just for you.
                    </p>
                )}
            </div>
        </div>
    );
}
