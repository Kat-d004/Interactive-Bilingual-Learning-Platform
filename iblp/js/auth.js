/**
 * auth.js — Authentication guard + logout wiring for every protected page.
 * Include BEFORE app.js on all pages except login.html.
 */

const AUTH_API_BASE = './api';

async function requireLogin() {
    try {
        const response = await fetch(`${AUTH_API_BASE}/auth-check.php`, { credentials: 'include' });
        const data = await response.json();
        if (!data.authenticated) {
            console.warn('⚠️ Not authenticated, redirecting to login');
            window.location.href = 'login.html';
            return false;
        }
        return true;
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = 'login.html';
        return false;
    }
}

function getCurrentChildId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('child_id') || sessionStorage.getItem('selected_child_id') || null;
}

async function logoutUser() {
    try {
        await fetch(`${AUTH_API_BASE}/logout.php`, { method: 'POST', credentials: 'include' });
    } catch (e) { console.error('Logout error:', e); }
    sessionStorage.clear();
    window.location.href = 'login.html';
}

function addLogoutHandler(selector = '.logout-btn') {
    document.querySelectorAll(selector).forEach(btn => {
        btn.addEventListener('click', e => { e.preventDefault(); logoutUser(); });
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    await requireLogin();
    addLogoutHandler('.logout-btn');
});
