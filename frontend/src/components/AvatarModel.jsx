import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

// Ready Player Me avatar with ARKit + Oculus Viseme morph targets
const AVATAR_URL =
    'https://models.readyplayer.me/638df693d72bffc6fa17943c.glb' +
    '?morphTargets=ARKit,Oculus%20Visemes&textureAtlas=1024&lod=0';

// ── Viseme mapping: word leading phoneme → RPM morph target ──────────────
const CONSONANT_VISEME = {
    p: 'viseme_PP', b: 'viseme_PP', m: 'viseme_PP',
    f: 'viseme_FF', v: 'viseme_FF',
    d: 'viseme_DD', t: 'viseme_DD',
    k: 'viseme_kk', g: 'viseme_kk',
    s: 'viseme_SS', z: 'viseme_SS',
    r: 'viseme_RR',
    n: 'viseme_nn', l: 'viseme_nn',
    j: 'viseme_CH', y: 'viseme_CH',
};
const VOWEL_VISEME = {
    a: 'viseme_aa', e: 'viseme_E', i: 'viseme_I', o: 'viseme_O', u: 'viseme_U',
};
const ALL_VISEMES = [
    'viseme_sil', 'viseme_PP', 'viseme_FF', 'viseme_TH',
    'viseme_DD', 'viseme_kk', 'viseme_CH', 'viseme_SS',
    'viseme_nn', 'viseme_RR', 'viseme_aa', 'viseme_E',
    'viseme_I', 'viseme_O', 'viseme_U',
];
const JAW_CANDIDATES = [
    'jawOpen', 'mouthOpen', 'Jaw_Open', 'mouth_open',
    'JawOpen', 'MouthOpen', 'viseme_aa',
];
const BROW_CANDIDATES = ['browInnerUp', 'browOuterUpLeft', 'browOuterUpRight'];
const SMILE_CANDIDATES = [
    'mouthSmile', 'mouthSmileLeft', 'mouthSmileRight',
    'mouthSmile_L', 'mouthSmile_R',
];

export function wordToViseme(word) {
    if (!word) return 'viseme_sil';
    const w = word.toLowerCase().replace(/[^a-z]/g, '');
    if (!w) return 'viseme_sil';
    if (w.startsWith('th')) return 'viseme_TH';
    if (w.startsWith('sh') || w.startsWith('ch')) return 'viseme_CH';
    const first = w[0];
    if (VOWEL_VISEME[first]) return VOWEL_VISEME[first];
    if (CONSONANT_VISEME[first]) return CONSONANT_VISEME[first];
    for (const ch of w) {
        if (VOWEL_VISEME[ch]) return VOWEL_VISEME[ch];
    }
    return 'viseme_aa';
}

// ── Resting pose — arm rotation to fix T-pose ────────────────────────────
// These are applied to ANY object whose name contains the keyword.
// RPM models use various naming: UpperArm, Arm, etc.
const RESTING_ROTATIONS = [
    // keyword-in-name → rotation [x, y, z] in radians
    { keyword: 'UpperArm', side: 'Right', rot: [0.2, 0, 1.1] },
    { keyword: 'UpperArm', side: 'Left', rot: [0.2, 0, -1.1] },
    { keyword: 'ForeArm', side: 'Right', rot: [0.4, 0, 0.3] },
    { keyword: 'ForeArm', side: 'Left', rot: [0.4, 0, -0.3] },
    { keyword: 'Hand', side: 'Right', rot: [0, 0, 0.1] },
    { keyword: 'Hand', side: 'Left', rot: [0, 0, -0.1] },
];

// 4 gesture poses — additional rotation ON TOP of resting pose
const GESTURE_DELTAS = [
    // 0: resting — no additional rotation
    {
        Right_UpperArm: [0, 0, 0], Left_UpperArm: [0, 0, 0],
        Right_ForeArm: [0, 0, 0], Left_ForeArm: [0, 0, 0]
    },
    // 1: right hand points forward/up
    {
        Right_UpperArm: [-0.6, 0, -0.8], Left_UpperArm: [0, 0, 0],
        Right_ForeArm: [-0.5, 0, -0.3], Left_ForeArm: [0, 0, 0]
    },
    // 2: both arms open wide — welcoming
    {
        Right_UpperArm: [0, 0, -0.5], Left_UpperArm: [0, 0, 0.5],
        Right_ForeArm: [0.3, 0, 0], Left_ForeArm: [0.3, 0, 0]
    },
    // 3: left hand raised
    {
        Right_UpperArm: [0, 0, 0], Left_UpperArm: [-0.6, 0, 0.8],
        Right_ForeArm: [0, 0, 0], Left_ForeArm: [-0.5, 0, 0.3]
    },
    // 4: right hand points at the board (sideways/forward)
    {
        Right_UpperArm: [-0.1, -0.6, -1.2], Left_UpperArm: [0, 0, 0.2],
        Right_ForeArm: [0, -0.4, -0.4], Left_ForeArm: [0.1, 0, 0]
    },
];

export function AvatarModel({ currentViseme, isSpeaking, agentState = 'idle' }) {
    const { scene } = useGLTF(AVATAR_URL);

    // Refs for animation state
    const blinkTimer = useRef(0);
    const breathTimer = useRef(0);
    const speakStart = useRef(0);
    const wasSpeaking = useRef(false);
    const gestureIdx = useRef(0);
    const gestureTimer = useRef(0);

    // Bone references: keyed by "Side_BoneType" e.g. "Right_UpperArm"
    const boneMap = useRef({});

    useEffect(() => {
        const bones = {};
        const allBoneNames = [];

        scene.traverse((obj) => {
            if (obj.isMesh) {
                obj.castShadow = true;
                obj.receiveShadow = true;
                if (obj.material) obj.material.envMapIntensity = 1.1;
            }

            // Log all bones (first time only)
            if (obj.isBone || obj.type === 'Bone' || obj.parent?.isSkinnedMesh) {
                allBoneNames.push(obj.name);
            }

            // Match bones by substring — covers all RPM naming variants
            if (obj.name) {
                const n = obj.name;
                for (const { keyword, side } of RESTING_ROTATIONS) {
                    if (n.includes(keyword) && n.includes(side)) {
                        const key = `${side}_${keyword}`;
                        if (!bones[key]) bones[key] = obj;
                    }
                }
            }
        });

        console.log('[AvatarModel] All scene object names:', allBoneNames.slice(0, 40));
        console.log('[AvatarModel] Cached bones:', Object.keys(bones));
        boneMap.current = bones;

        // Apply resting rotations immediately so arms drop from T-pose
        for (const { keyword, side, rot } of RESTING_ROTATIONS) {
            const key = `${side}_${keyword}`;
            const bone = bones[key];
            if (bone) {
                bone.rotation.x = rot[0];
                bone.rotation.y = rot[1];
                bone.rotation.z = rot[2];
            }
        }
    }, [scene]);

    useFrame((state, delta) => {
        const t = state.clock.elapsedTime;
        blinkTimer.current += delta;
        breathTimer.current += delta;

        // Track speak start
        if (isSpeaking && !wasSpeaking.current) {
            speakStart.current = t;
            wasSpeaking.current = true;
        } else if (!isSpeaking) {
            wasSpeaking.current = false;
        }
        const tSpeak = isSpeaking ? (t - speakStart.current) : 0;

        // ── Gesture cycling while explaining ─────────────────────────────
        if (isSpeaking || agentState === 'pointBoard') {
            if (agentState === 'pointBoard') {
                gestureIdx.current = 4; // Force pointBoard gesture
            } else {
                gestureTimer.current += delta;
                if (gestureTimer.current > 2.2) {
                    gestureTimer.current = 0;
                    gestureIdx.current = (gestureIdx.current + 1) % GESTURE_DELTAS.length;
                    // Skip pointBoard (4) in random cycle unless explicitly set
                    if (gestureIdx.current === 4) gestureIdx.current = 0;
                }
            }
        } else {
            gestureTimer.current = 0;
            if (gestureIdx.current !== 0) gestureIdx.current = 0;
        }

        const gd = GESTURE_DELTAS[gestureIdx.current];
        const lerpSpd = delta * 2.5;
        const osc = isSpeaking ? Math.sin(t * 2.5) * 0.03 : 0;

        // Apply resting + gesture delta to each bone
        for (const { keyword, side, rot: rest } of RESTING_ROTATIONS) {
            const key = `${side}_${keyword}`;
            const bone = boneMap.current[key];
            if (!bone) continue;

            const gdKey = `${side}_${keyword}`;
            const delta_rot = gd[gdKey] || [0, 0, 0];

            const tx = rest[0] + delta_rot[0] + osc;
            const ty = rest[1] + delta_rot[1];
            const tz = rest[2] + delta_rot[2];

            bone.rotation.x = THREE.MathUtils.lerp(bone.rotation.x, tx, lerpSpd);
            bone.rotation.y = THREE.MathUtils.lerp(bone.rotation.y, ty, lerpSpd);
            bone.rotation.z = THREE.MathUtils.lerp(bone.rotation.z, tz, lerpSpd);
        }

        // ── Morph targets (face) ──────────────────────────────────────────
        scene.traverse((obj) => {
            if (!obj.isMesh || !obj.morphTargetDictionary || !obj.morphTargetInfluences) return;
            const dict = obj.morphTargetDictionary;

            // Jaw open/close while speaking
            let jawIdx;
            for (const name of JAW_CANDIDATES) {
                if (dict[name] !== undefined) { jawIdx = dict[name]; break; }
            }
            if (jawIdx !== undefined) {
                let jawTarget = 0;
                if (isSpeaking) {
                    const rhythm = Math.abs(Math.sin(tSpeak * 4.5));
                    const amplitude = 0.28 + Math.sin(tSpeak * 1.3) * 0.14;
                    jawTarget = Math.max(0, Math.min(0.55, rhythm * amplitude));
                }
                obj.morphTargetInfluences[jawIdx] = THREE.MathUtils.lerp(
                    obj.morphTargetInfluences[jawIdx], jawTarget, delta * 12
                );
            }

            // Polly viseme shapes
            const activeViseme = isSpeaking ? (currentViseme || 'viseme_aa') : 'viseme_sil';
            for (const v of ALL_VISEMES) {
                const vIdx = dict[v];
                if (vIdx === undefined || vIdx === jawIdx) continue;
                const want = (v === activeViseme && isSpeaking) ? 0.75 : 0;
                obj.morphTargetInfluences[vIdx] = THREE.MathUtils.lerp(
                    obj.morphTargetInfluences[vIdx], want, delta * 16
                );
            }

            // Natural blink every ~3.5s
            const blinkPhase = blinkTimer.current % 3.5;
            const blinkVal = blinkPhase < 0.08 ? 1 : 0;
            for (const name of ['eyesClosed', 'eyeBlinkLeft', 'eyesBlinkLeft', 'Eye_Blink_L']) {
                const idx = dict[name];
                if (idx !== undefined) obj.morphTargetInfluences[idx] = blinkVal;
            }
            for (const name of ['eyeBlinkRight', 'eyesBlinkRight', 'Eye_Blink_R']) {
                const idx = dict[name];
                if (idx !== undefined) obj.morphTargetInfluences[idx] = blinkVal;
            }

            // Eyebrow raise
            const browTarget = (agentState === 'explaining')
                ? 0.2 + Math.abs(Math.sin(t * 2.5)) * 0.2
                : (agentState === 'thinking') ? 0.4 : 0;
            for (const name of BROW_CANDIDATES) {
                const idx = dict[name];
                if (idx !== undefined) {
                    obj.morphTargetInfluences[idx] = THREE.MathUtils.lerp(
                        obj.morphTargetInfluences[idx], browTarget, delta * 4
                    );
                }
            }

            // Idle smile
            const smileTarget = (!isSpeaking && agentState === 'idle') ? 0.12 : 0;
            for (const name of SMILE_CANDIDATES) {
                const idx = dict[name];
                if (idx !== undefined) {
                    obj.morphTargetInfluences[idx] = THREE.MathUtils.lerp(
                        obj.morphTargetInfluences[idx], smileTarget, delta * 2.5
                    );
                }
            }

            // Breathing
            obj.position.y = Math.sin(breathTimer.current * 0.5) * 0.0025;
        });

        // ── Head idle sway ─────────────────────────────────────────────────
        scene.rotation.y = Math.sin(t * 0.28) * 0.04;
        scene.rotation.x = Math.sin(t * 0.19) * 0.010;
        if (isSpeaking) {
            scene.rotation.x += Math.sin(tSpeak * 5.5) * 0.005;
            scene.rotation.z = Math.sin(tSpeak * 3.2) * 0.008;
        } else if (agentState === 'thinking') {
            scene.rotation.x = Math.sin(t * 0.9) * 0.02;
            scene.rotation.z = Math.sin(t * 0.7) * 0.012;
        } else {
            scene.rotation.z = THREE.MathUtils.lerp(scene.rotation.z, 0, delta * 3);
        }
    });

    return (
        <primitive
            object={scene}
            scale={2.2}
            position={[0, -2.1, 0]}
        />
    );
}

useGLTF.preload(AVATAR_URL);
