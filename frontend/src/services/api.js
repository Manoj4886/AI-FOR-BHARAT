import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE_URL });

export const askQuestion = (question, skillLevel, userId) =>
    api.post('/ask', { question, skill_level: skillLevel, user_id: userId }).then(r => r.data);

export const askQuestionWithFile = (question, skillLevel, userId, file) => {
    const form = new FormData();
    form.append('question', question);
    form.append('skill_level', skillLevel);
    form.append('user_id', userId);
    form.append('file', file);
    return api.post('/ask-with-file', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
};

export const generateQuiz = (topic, skillLevel, numQuestions = 5) =>
    api.post('/quiz', { topic, skill_level: skillLevel, num_questions: numQuestions }).then(r => r.data);

export const postProgress = (userId, eventType, data) =>
    api.post('/progress', { user_id: userId, event_type: eventType, data }).then(r => r.data);

export const getProgress = (userId) =>
    api.get('/progress', { params: { user_id: userId } }).then(r => r.data);

// ── Computer Vision ────────────────────────────────────────────────────────
export const generateImage = (prompt) =>
    api.post('/vision/generate-image', { prompt }).then(r => r.data);

export const generateVideo = (imageB64, topic, spokenText) =>
    api.post('/vision/generate-video', {
        image_b64: imageB64,
        topic,
        spoken_text: spokenText,
    }).then(r => r.data);

// ── Recommendations ─────────────────────────────────────────────────────────
export const getRecommendations = (userId) =>
    api.get(`/recommendations/${userId}`).then(r => r.data);

export const getAllTopics = () =>
    api.get('/recommendations/topics/all').then(r => r.data);

// ── DeepLens + Kinesis Video Streams ────────────────────────────────────────
export const getVideoPipelineStatus = () =>
    api.get('/video-stream/status').then(r => r.data);

export const listVideoStreams = () =>
    api.get('/video-stream/streams').then(r => r.data);

export const getHlsStreamUrl = (streamName, live = true) =>
    api.get(`/video-stream/hls/${streamName}`, { params: { live } }).then(r => r.data);

export const getDashStreamUrl = (streamName) =>
    api.get(`/video-stream/dash/${streamName}`).then(r => r.data);

export const describeStream = (streamName) =>
    api.get(`/video-stream/describe/${streamName}`).then(r => r.data);

export const extractStreamClip = (streamName, startSecondsAgo = 60, durationSeconds = 30) =>
    api.post(`/video-stream/clip/${streamName}`, {
        start_seconds_ago: startSecondsAgo,
        duration_seconds: durationSeconds,
    }).then(r => r.data);

export const getDeepLensInference = (streamName) =>
    api.get(`/video-stream/inference/${streamName}`).then(r => r.data);

export const startStreamAnalysis = (streamName) =>
    api.post(`/video-stream/analyze/${streamName}`).then(r => r.data);

export const createVideoStream = (streamName = null) =>
    api.post('/video-stream/create', { stream_name: streamName }).then(r => r.data);

// ── Amazon Q / AI Assist ────────────────────────────────────────────────────
export const reviewContent = (content, topic, contentType = 'explanation') =>
    api.post('/ai-assist/review', { content, topic, content_type: contentType }).then(r => r.data);

export const getExpertAnswer = (question, context = '') =>
    api.post('/ai-assist/expert-answer', { question, context }).then(r => r.data);

export const scoreContent = (content) =>
    api.post('/ai-assist/score', { content }).then(r => r.data);

export const getAiAssistStatus = () =>
    api.get('/ai-assist/status').then(r => r.data);

// ── Augmented AI / Human Review ─────────────────────────────────────────────
export const startHumanReview = (content, topic, reviewType = 'content_accuracy', confidenceScore = 0.5) =>
    api.post('/human-review/start', { content, topic, review_type: reviewType, confidence_score: confidenceScore }).then(r => r.data);

export const getReviewStatus = (reviewId) =>
    api.get(`/human-review/status/${reviewId}`).then(r => r.data);

export const submitReviewDecision = (reviewId, decision, reviewerNotes = '', correctedContent = '') =>
    api.post('/human-review/decide', { review_id: reviewId, decision, reviewer_notes: reviewerNotes, corrected_content: correctedContent }).then(r => r.data);

export const getPendingReviews = () =>
    api.get('/human-review/pending').then(r => r.data);

export const getReviewStats = () =>
    api.get('/human-review/stats').then(r => r.data);

// ── AWS Security Hub ────────────────────────────────────────────────────────
export const getSecurityFindings = (maxResults = 20) =>
    api.get('/security/findings', { params: { max_results: maxResults } }).then(r => r.data);

export const getComplianceStatus = () =>
    api.get('/security/compliance').then(r => r.data);

export const getSecurityScore = () =>
    api.get('/security/score').then(r => r.data);

export const logSecurityEvent = (eventType, severity = 'LOW', description = '', userId = '') =>
    api.post('/security/event', { event_type: eventType, severity, description, user_id: userId }).then(r => r.data);

export const getSecurityEvents = (limit = 50) =>
    api.get('/security/events', { params: { limit } }).then(r => r.data);

export const getSecuritySummary = () =>
    api.get('/security/summary').then(r => r.data);

// ── AWS SageMaker / Visualization ───────────────────────────────────────────
export const getVisualizationDashboard = (userId = '') =>
    api.get('/sagemaker/dashboard', { params: { user_id: userId } }).then(r => r.data);

export const getLearningTimeline = (userId = '', days = 7) =>
    api.get('/sagemaker/timeline', { params: { user_id: userId, days } }).then(r => r.data);

export const getTopicHeatmap = () =>
    api.get('/sagemaker/heatmap').then(r => r.data);

export const getPerformanceRadar = (userId = '') =>
    api.get('/sagemaker/radar', { params: { user_id: userId } }).then(r => r.data);

export const getTopicDistribution = () =>
    api.get('/sagemaker/distribution').then(r => r.data);

export const getProgressSparkline = (userId = '', metric = 'score') =>
    api.get('/sagemaker/sparkline', { params: { user_id: userId, metric } }).then(r => r.data);

export const trackLearningEvent = (userId, eventType, topic = '', score = 0) =>
    api.post('/sagemaker/track', { user_id: userId, event_type: eventType, topic, score }).then(r => r.data);

export const invokeSagemakerEndpoint = (endpointName, payload = {}) =>
    api.post('/sagemaker/invoke', { endpoint_name: endpointName, payload }).then(r => r.data);

export const listSagemakerEndpoints = () =>
    api.get('/sagemaker/endpoints').then(r => r.data);

// ── Conversational AI ───────────────────────────────────────────────────────
export const getConversationHistory = (sessionId) =>
    api.get(`/conversation/history/${sessionId}`).then(r => r.data);

export const clearConversation = (sessionId) =>
    api.delete(`/conversation/clear/${sessionId}`).then(r => r.data);

export const updateVoiceSettings = (sessionId, voiceEnabled = true, voiceSpeed = 1.0, voiceName = 'auto', language = 'en') =>
    api.post('/conversation/voice-settings', { session_id: sessionId, voice_enabled: voiceEnabled, voice_speed: voiceSpeed, voice_name: voiceName, language }).then(r => r.data);

export const listConversationSessions = () =>
    api.get('/conversation/sessions').then(r => r.data);

export const getConversationStatus = () =>
    api.get('/conversation/status').then(r => r.data);

// ── Avatar Engines (Unity / Unreal / Three.js) ──────────────────────────────
export const listAvatarEngines = () =>
    api.get('/avatars/engines').then(r => r.data);

export const getAvatarEngineInfo = (engine) =>
    api.get(`/avatars/engines/${engine}`).then(r => r.data);

export const createAvatar = (sessionId, engine, avatarUrl = '', settings = null) =>
    api.post('/avatars/create', { session_id: sessionId, engine, avatar_url: avatarUrl, settings }).then(r => r.data);

export const getAvatarState = (sessionId) =>
    api.get(`/avatars/state/${sessionId}`).then(r => r.data);

export const setAvatarAnimation = (sessionId, state, blendTime = 0.3) =>
    api.post('/avatars/animate', { session_id: sessionId, state, blend_time: blendTime }).then(r => r.data);

export const setAvatarExpression = (sessionId, expression, intensity = 1.0) =>
    api.post('/avatars/expression', { session_id: sessionId, expression, intensity }).then(r => r.data);

export const setAvatarViseme = (sessionId, viseme) =>
    api.post('/avatars/viseme', { session_id: sessionId, viseme }).then(r => r.data);

export const setAvatarEyeTarget = (sessionId, x, y, z) =>
    api.post('/avatars/eye-target', { session_id: sessionId, x, y, z }).then(r => r.data);

export const setAvatarHeadRotation = (sessionId, pitch, yaw, roll) =>
    api.post('/avatars/head-rotation', { session_id: sessionId, pitch, yaw, roll }).then(r => r.data);

export const setAvatarGesture = (sessionId, gesture) =>
    api.post('/avatars/gesture', { session_id: sessionId, gesture }).then(r => r.data);

export const listAvatarGestures = () =>
    api.get('/avatars/gestures').then(r => r.data);

export const updateAvatarRenderSettings = (sessionId, settings) =>
    api.post('/avatars/render-settings', { session_id: sessionId, ...settings }).then(r => r.data);

// ── AWS Generative AI Video ─────────────────────────────────────────────────
export const listGenVideoModels = () =>
    api.get('/gen-video/models').then(r => r.data);

export const getGenVideoModelInfo = (modelId) =>
    api.get(`/gen-video/models/${modelId}`).then(r => r.data);

export const generateTextToVideo = (prompt, topic = 'General', durationSeconds = 6, cameraMotion = 'static', style = 'educational') =>
    api.post('/gen-video/text-to-video', { prompt, topic, duration_seconds: durationSeconds, camera_motion: cameraMotion, style }).then(r => r.data);

export const generateImageToVideo = (imageB64, prompt = '', topic = 'General', motionStrength = 0.7) =>
    api.post('/gen-video/image-to-video', { image_b64: imageB64, prompt, topic, motion_strength: motionStrength }).then(r => r.data);

export const planVideoScenes = (topic, durationSeconds = 30, numScenes = 5, style = 'educational') =>
    api.post('/gen-video/plan-scenes', { topic, duration_seconds: durationSeconds, num_scenes: numScenes, style }).then(r => r.data);

export const getGenVideoJobStatus = (jobId) =>
    api.get(`/gen-video/jobs/${jobId}`).then(r => r.data);

export const listGenVideoJobs = () =>
    api.get('/gen-video/jobs').then(r => r.data);

export const getGenVideoStatus = () =>
    api.get('/gen-video/status').then(r => r.data);

// ── Amazon Nova Reel ─────────────────────────────────────────────────────────
export const novaReelGenerate = (prompt, topic = '', cameraMotion = 'static', style = 'educational', duration = 6, seed = 0) =>
    api.post('/nova-reel/generate', { prompt, topic, camera_motion: cameraMotion, style, duration, seed }).then(r => r.data);

export const novaReelStoryboard = (topic, numShots = 4, style = 'educational') =>
    api.post('/nova-reel/storyboard', { topic, num_shots: numShots, style }).then(r => r.data);

export const novaReelCameraMotions = () =>
    api.get('/nova-reel/camera-motions').then(r => r.data);

export const novaReelStyles = () =>
    api.get('/nova-reel/styles').then(r => r.data);

export const novaReelJobStatus = (jobId) =>
    api.get(`/nova-reel/jobs/${jobId}`).then(r => r.data);

export const novaReelListJobs = () =>
    api.get('/nova-reel/jobs').then(r => r.data);

export const novaReelStatus = () =>
    api.get('/nova-reel/status').then(r => r.data);

// ── AWS Elemental MediaConvert ───────────────────────────────────────────────
export const mcTranscode = (inputS3Uri, outputFormat = 'mp4', resolution = '1080p', audioPreset = 'narration', captionFile = '', captionFormat = 'srt', watermarkText = '', thumbnail = true) =>
    api.post('/mediaconvert/transcode', { input_s3_uri: inputS3Uri, output_format: outputFormat, resolution, audio_preset: audioPreset, caption_file: captionFile, caption_format: captionFormat, watermark_text: watermarkText, thumbnail }).then(r => r.data);

export const mcAdaptiveStream = (inputS3Uri, streamType = 'hls', resolutions = null) =>
    api.post('/mediaconvert/adaptive-stream', { input_s3_uri: inputS3Uri, stream_type: streamType, resolutions }).then(r => r.data);

export const mcThumbnails = (inputS3Uri, intervalSeconds = 5, width = 320, height = 180, format = 'jpg') =>
    api.post('/mediaconvert/thumbnails', { input_s3_uri: inputS3Uri, interval_seconds: intervalSeconds, width, height, format }).then(r => r.data);

export const mcCaptions = (inputS3Uri, captionS3Uri, captionFormat = 'srt', language = 'en') =>
    api.post('/mediaconvert/captions', { input_s3_uri: inputS3Uri, caption_s3_uri: captionS3Uri, caption_format: captionFormat, language }).then(r => r.data);

export const mcFormats = () => api.get('/mediaconvert/formats').then(r => r.data);
export const mcResolutions = () => api.get('/mediaconvert/resolutions').then(r => r.data);
export const mcAudioPresets = () => api.get('/mediaconvert/audio-presets').then(r => r.data);
export const mcCaptionFormats = () => api.get('/mediaconvert/caption-formats').then(r => r.data);

export const mcJobStatus = (jobId) => api.get(`/mediaconvert/jobs/${jobId}`).then(r => r.data);
export const mcListJobs = () => api.get('/mediaconvert/jobs').then(r => r.data);
export const mcStatus = () => api.get('/mediaconvert/status').then(r => r.data);
