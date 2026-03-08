import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import {
    Environment,
    OrbitControls,
    ContactShadows,
    PerspectiveCamera,
    Html,
} from '@react-three/drei';
import { AvatarModel } from './AvatarModel';

const STATE_LABELS = {
    idle: '👨‍🏫 AI Tutor',
    listening: '🎙 Listening…',
    thinking: '💭 Thinking…',
    explaining: '🗣 Explaining',
};
const STATE_COLORS = {
    idle: '#6366f1',
    listening: '#10b981',
    thinking: '#f59e0b',
    explaining: '#818cf8',
};

function LoadingFallback() {
    return (
        <Html center>
            <div style={{
                color: '#818cf8',
                fontSize: '13px',
                fontFamily: 'Inter, sans-serif',
                textAlign: 'center',
                opacity: 0.7,
            }}>
                Loading Avatar…
            </div>
        </Html>
    );
}

export default function Avatar({ isSpeaking, currentViseme, agentState = 'idle' }) {
    const stateColor = STATE_COLORS[agentState] || STATE_COLORS.idle;

    return (
        <div className="avatar-wrapper" style={{ '--state-color': stateColor }}>
            {/* Animated glow ring */}
            <div className={`avatar-glow ${isSpeaking ? 'speaking' : ''} glow-${agentState}`} />

            <div className="avatar-canvas-container">
                <Canvas
                    shadows
                    gl={{ antialias: true, alpha: true }}
                    style={{ width: '100%', height: '100%', background: 'transparent' }}
                >
                    {/*
                      Head+shoulders shot:
                      fov=40 wide enough to see neck+shoulders.
                      camera y=1.45 → looks at upper chest area.
                      z=2.8 → enough distance to show shoulders without cropping.
                    */}
                    <PerspectiveCamera makeDefault fov={40} position={[0, 1.45, 2.8]} />

                    {/* ── 3-point studio lighting ─────────────────────────── */}
                    {/* Key light: warm, front-right */}
                    <directionalLight
                        castShadow
                        intensity={1.6}
                        position={[2.5, 3.5, 2.5]}
                        color="#fff8f0"
                        shadow-mapSize={[1024, 1024]}
                    />
                    {/* Fill light: cool, left */}
                    <directionalLight
                        intensity={0.6}
                        position={[-3, 2, 1.5]}
                        color="#d0e8ff"
                    />
                    {/* Rim / back light: purple accent */}
                    <pointLight
                        intensity={1.2}
                        position={[-1, 3.5, -2]}
                        color="#7c3aed"
                    />
                    {/* Ambient fill so shadows aren't pitch black */}
                    <ambientLight intensity={0.45} />
                    {/* Subtle indigo eye-level fill */}
                    <pointLight position={[0, 1.5, 3]} intensity={0.3} color="#818CF8" />

                    {/* Studio HDRI */}
                    <Environment preset="studio" background={false} />

                    {/* Avatar */}
                    <Suspense fallback={<LoadingFallback />}>
                        <AvatarModel
                            isSpeaking={isSpeaking}
                            currentViseme={currentViseme}
                            agentState={agentState}
                        />
                    </Suspense>

                    {/* Ground shadow */}
                    <ContactShadows
                        position={[0, -0.95, 0]}
                        opacity={0.5}
                        scale={4}
                        blur={2.5}
                        far={3}
                    />

                    {/* Subtle mouse-drag interaction */}
                    <OrbitControls
                        enablePan={false}
                        enableZoom={false}
                        minPolarAngle={Math.PI / 3}
                        maxPolarAngle={Math.PI / 1.8}
                        minAzimuthAngle={-0.35}
                        maxAzimuthAngle={0.35}
                        target={[0, 1.45, 0]}
                    />
                </Canvas>
            </div>

            {/* Cinematic status badge */}
            <div
                className={`avatar-status active`}
                style={{ '--badge-color': stateColor }}
            >
                <span
                    className={`avatar-status-dot ${agentState !== 'idle' ? 'pulsing' : ''}`}
                    style={{ background: stateColor }}
                />
                {STATE_LABELS[agentState] || STATE_LABELS.idle}
            </div>

            {/* Speaking waveform overlay */}
            {isSpeaking && (
                <div className="avatar-waveform">
                    {Array.from({ length: 12 }).map((_, i) => (
                        <span
                            key={i}
                            className="wv-bar"
                            style={{ animationDelay: `${i * 0.07}s` }}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
