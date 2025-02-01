<template>
<div id="app">
    <div class="auth-wrapper" v-if="!isAuthenticated">
    <div class="login-container">
        <h1 class="app-title">Budget App</h1>
        <Login 
        @login-success="handleLoginSuccess"
        @login-error="handleLoginError"
        />
        <div v-if="error" class="error-message">{{ error }}</div>
    </div>
    </div>
    <div v-else class="main-content">
    <nav class="nav-bar">
        <h1>Budget App</h1>
        <div class="nav-links">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/transactions">Transactions</router-link>
        <router-link to="/categories">Categories</router-link>
        </div>
        <div class="user-section">
        <span class="user-email" v-if="user">{{ user.email }}</span>
        <button @click="handleLogout" class="logout-btn">Logout</button>
        </div>
    </nav>
    <main class="content-area">
        <router-view />
    </main>
    </div>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
import Login from './components/Login.vue';

const router = useRouter();
const auth = getAuth();
const isAuthenticated = ref(false);
const user = ref(null);
const error = ref(null);

onMounted(() => {
onAuthStateChanged(auth, (userData) => {
    isAuthenticated.value = !!userData;
    user.value = userData;
    if (userData) {
    console.log('User is signed in:', userData.email);
    router.push('/dashboard');
    } else {
    router.push('/login');
    }
});
});

const handleLoginSuccess = () => {
error.value = null;
};

const handleLoginError = (err) => {
error.value = err.message;
console.error('Login error:', err);
};

const handleLogout = async () => {
try {
    await signOut(auth);
    router.push('/login');
} catch (err) {
    console.error('Logout error:', err);
    error.value = 'Failed to logout. Please try again.';
}
};
</script>

<style>
#app {
font-family: var(--font-family);
-webkit-font-smoothing: antialiased;
-moz-osx-font-smoothing: grayscale;
color: var(--text-color);
height: 100vh;
width: 100vw;
display: flex;
flex-direction: column;
}

.auth-wrapper {
display: flex;
justify-content: center;
align-items: center;
min-height: 100vh;
background: var(--background-color, #f5f5f5);
}

.login-container {
width: 100%;
max-width: 400px;
padding: 2rem;
text-align: center;
}

.app-title {
margin-bottom: 2rem;
color: var(--primary-color, #2c3e50);
font-size: 2rem;
}

.main-content {
flex: 1;
display: flex;
flex-direction: column;
height: 100vh;
}

.nav-bar {
display: flex;
justify-content: space-between;
align-items: center;
padding: 1rem 2rem;
background: var(--primary-color, #2c3e50);
color: white;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-links {
display: flex;
gap: 2rem;
}

.nav-links a {
color: white;
text-decoration: none;
padding: 0.5rem 1rem;
border-radius: 4px;
transition: background 0.3s ease;
}

.nav-links a:hover,
.nav-links a.router-link-active {
background: rgba(255, 255, 255, 0.1);
}

.user-section {
display: flex;
align-items: center;
gap: 1rem;
}

.user-email {
color: rgba(255, 255, 255, 0.8);
font-size: 0.9rem;
}

.content-area {
flex: 1;
padding: 2rem;
overflow-y: auto;
background: var(--background-color, #f5f5f5);
}

.error-message {
margin-top: 1rem;
padding: 0.75rem;
border-radius: 4px;
background: var(--error-color, #dc3545);
color: white;
}

.logout-btn {
padding: 0.5rem 1rem;
border: none;
border-radius: 4px;
background: rgba(255, 255, 255, 0.1);
color: white;
cursor: pointer;
transition: background 0.3s ease;
}

.logout-btn:hover {
background: rgba(255, 255, 255, 0.2);
}
</style>
