/**
 * app.js — IBLP application core (backend/DB version)
 * Handles progress, preferences, quiz scores, stars, language.
 * Requires auth.js to be loaded first.
 */

const API_BASE = './api';

// ── Child ID ─────────────────────────────────────────────────────────────────
function getChildId() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('child_id') || sessionStorage.getItem('selected_child_id');
    if (!id) { window.location.href = 'login.html'; }
    return id;
}

// ── Global state ─────────────────────────────────────────────────────────────
let child_id = null;
let progress  = {
    totalStars: 0,
    colors_completed: false,  colors_attempts: 0,
    numbers_completed: false, numbers_attempts: 0,
    animals_completed: false, animals_attempts: 0
};
let currentLanguage     = 'en';
let currentPreferences  = {};

// ── Speech synthesis ──────────────────────────────────────────────────────────
let isPlaying = false;

function playRecording(fileName) {
    const audio = new Audio(`recordings/${fileName}.wav`);
    audio.play().catch(err => {
        console.error("Audio play failed:", err);
    });
}

function speak(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.8;
        utterance.pitch = 1.1;
        utterance.onstart = () => { isPlaying = true; };
        utterance.onend = () => { isPlaying = false; };
        window.speechSynthesis.speak(utterance);
    }
}

// ── Audio feedback ────────────────────────────────────────────────────────────
function playFeedbackSound(isCorrect) {
    const ctx  = new (window.AudioContext || window.webkitAudioContext)();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    if (isCorrect) {
        osc.frequency.setValueAtTime(523.25, ctx.currentTime);
        osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.1);
        osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.2);
    } else {
        osc.frequency.setValueAtTime(392,    ctx.currentTime);
        osc.frequency.setValueAtTime(329.63, ctx.currentTime + 0.15);
    }
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.3);
}

// ── API: progress ─────────────────────────────────────────────────────────────
async function loadProgress() {
    try {
        const r = await fetch(`${API_BASE}/progress.php?child_id=${child_id}`, { credentials: 'include' });
        const d = await r.json();
        if (d.success && d.progress) {
            progress = {
                totalStars:        d.progress.total_stars       || 0,
                colors_completed:  !!d.progress.colors_completed,
                colors_attempts:   d.progress.colors_attempts   || 0,
                numbers_completed: !!d.progress.numbers_completed,
                numbers_attempts:  d.progress.numbers_attempts  || 0,
                animals_completed: !!d.progress.animals_completed,
                animals_attempts:  d.progress.animals_attempts  || 0
            };
            updateStarsDisplay();
            return true;
        }
    } catch (e) { console.error('Error loading progress:', e); }
    return false;
}

async function saveProgress() {
    if (!child_id) return;
    try {
        await fetch(`${API_BASE}/progress.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                child_id,
                total_stars:       progress.totalStars,
                colors_completed:  progress.colors_completed,
                colors_attempts:   progress.colors_attempts,
                numbers_completed: progress.numbers_completed,
                numbers_attempts:  progress.numbers_attempts,
                animals_completed: progress.animals_completed,
                animals_attempts:  progress.animals_attempts
            })
        });
    } catch (e) { console.error('Error saving progress:', e); }
}

// ── API: preferences ──────────────────────────────────────────────────────────
async function loadPreferences() {
    try {
        const r = await fetch(`${API_BASE}/preferences.php?child_id=${child_id}`, { credentials: 'include' });
        const d = await r.json();
        if (d.success && d.preferences) {
            currentPreferences = d.preferences;
            currentLanguage    = d.preferences.language || 'en';
            return true;
        }
    } catch (e) { console.error('Error loading preferences:', e); }
    return false;
}

async function savePreferences(prefs) {
    try {
        await fetch(`${API_BASE}/preferences.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ child_id, ...prefs })
        });
    } catch (e) { console.error('Error saving preferences:', e); }
}

// ── API: activity log ─────────────────────────────────────────────────────────
async function logActivity(activity_type, module = null, details = {}) {
    try {
        await fetch(`${API_BASE}/activity.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ child_id, activity_type, module, details })
        });
    } catch (e) { console.error('Error logging activity:', e); }
}

// ── API: quiz scores ──────────────────────────────────────────────────────────
async function submitQuizScore(quiz_category, score, total_questions = 10) {
    try {
        const r = await fetch(`${API_BASE}/quiz.php`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ child_id, quiz_category, score, total_questions })
        });
        const d = await r.json();
        if (d.success && d.percentage >= 70) {
            progress.totalStars += Math.ceil(d.percentage / 20);
            updateStarsDisplay();
        }
        return d;
    } catch (e) { console.error('Error submitting quiz score:', e); return null; }
}

// ── Stars display ─────────────────────────────────────────────────────────────
function updateStarsDisplay() {
    document.querySelectorAll('.stars-count').forEach(el => {
        el.textContent = progress.totalStars;
    });
}

function addStars(count) {
    if (!child_id) return;
    progress.totalStars += count;
    updateStarsDisplay();
}

function completeTopic(topic) {
    const key = topic + '_completed';
    const att = topic + '_attempts';
    if (key in progress) {
        progress[key] = true;
        progress[att] = (progress[att] || 0) + 1;
        saveProgress();
    }
}

// Called by quiz pages at the end of a quiz.
// Updates attempts/completed in student_progress AND posts score to quiz.php.
function addQuizScore(topic, score, totalQuestions = 5) {
    const attKey  = topic + '_attempts';
    const compKey = topic + '_completed';
    if (attKey in progress) {
        progress[attKey]  = (progress[attKey] || 0) + 1;
        progress[compKey] = true;
    }
    saveProgress();                                // persist attempts + completed
    submitQuizScore(topic, score, totalQuestions); // post score row to quiz_scores
}

// ── Language ──────────────────────────────────────────────────────────────────
async function toggleLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'st' : 'en';
    await savePreferences({ language: currentLanguage });
    document.querySelectorAll('.lang-toggle').forEach(btn => {
        btn.textContent = currentLanguage === 'en' ? 'Sesotho' : 'English';
    });
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: currentLanguage } }));
    logActivity('language_changed', null, { language: currentLanguage });
    return currentLanguage;
}

async function handleLanguageToggle(e) {
    e.preventDefault();
    await toggleLanguage();
}

function handleSpeak(e) {
    e.preventDefault();

    const text = e.currentTarget.getAttribute('data-text');
    const file = e.currentTarget.getAttribute('data-audio');

    if (currentLanguage === 'st' && file) {
        // Play recorded Sesotho audio
        playRecording(file);
    } else if (text) {
        // Use TTS for English
        speak(text);
    }
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    child_id = getChildId();
    console.log('👧 Child ID:', child_id);

    const [prefsOk, progOk] = await Promise.all([loadPreferences(), loadProgress()]);
    if (!prefsOk || !progOk) console.warn('⚠️ Could not load some data from backend');
    
    window.dispatchEvent(new CustomEvent('progressLoaded', { detail: { progress } }));

    document.querySelectorAll('.lang-toggle').forEach(btn => {
        btn.textContent = currentLanguage === 'en' ? 'Sesotho' : 'English';
        btn.removeEventListener('click', handleLanguageToggle);
        btn.addEventListener('click', handleLanguageToggle);
    });
    document.querySelectorAll('.speak-btn').forEach(btn => {
        btn.removeEventListener('click', handleSpeak);
        btn.addEventListener('click', handleSpeak);
    });

    console.log('📊 Progress:', progress);
    console.log('🌐 Language:', currentLanguage);
});
