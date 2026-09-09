
const API_URL = 'http://localhost:8000/api/v1';

let state = {
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    currentProject: null
};

console.log('frontend/app.js: loaded');

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded', {token: state.token, user: state.user});
    if (state.token && state.user) {
        showMainInterface();
        loadProjects();
    } else {
        showLoginForm();
    }

    const loginFromEl = document.getElementById('loginForm');

    if (loginFromEl) {
        console.log('Attaching loginFrom submit handler');
        loginFromEl.addEventListener('submit', handleLogin);
    } else{
        console.error('loginForm element not found');
    }

});

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    errorEl.textContent = '';
    console.log('handleLogin called', {email});

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json'},
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json()
            console.error('login response error', error);
            throw new Error(error.detail || "Ошибка авторизации");
        }

        const data = await response.json();
        state.token = data.access_token;
        localStorage.setItem('token', state.token);

        await fetchCurrentUser();

        showMainInterface();
        loadProjects();

    } catch (err) {
        errorEl.textContent = err.message;
    }
}

async function fetchCurrentUser() {
    const response = await fetch(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (response.ok) {
        state.user = await response.json();
        localStorage.setItem('user', JSON.stringify(state.user));
    }
}

function logout() {
    state.token = null;
    state.user = null;
    state.currentProject = null;

    localStorage.removeItem('token');
    localStorage.removeItem('user');
    showLoginForm();
}


function showLoginForm() {
    document.getElementById('loginSection').style.display = 'flex';
    document.getElementById('mainSection').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
}





