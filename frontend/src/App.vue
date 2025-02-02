<template>
<div id="app">
    <div class="auth-wrapper" v-if="!isAuthenticated && currentRoute !== '/greeting'">
    <div class="login-container">
        <h1 class="app-title">Budget App</h1>
        <Login 
        @login-success="handleLoginSuccess"
        @login-error="handleLoginError"
        />
        <div v-if="error" class="error-message">{{ error }}</div>
        <div class="greeting-link">
            <router-link to="/greeting" class="greeting-button">Try Greeting Demo</router-link>
        </div>
    </div>
    </div>
    <div v-else class="main-content">
        <SideMenu 
            :user="user"
            @logout="handleLogout"
        />
        <main class="content-area">
            <router-view />
        </main>
    </div>
</div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
import Login from './components/Login.vue';
import SideMenu from './components/SideMenu.vue';

const router = useRouter();
const route = useRoute();
const auth = getAuth();
const currentRoute = computed(() => route.path);
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
background-color: #f0f2f5;
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
    flex-direction: row;
    height: 100vh;
    overflow: hidden;
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
    height: 100vh;
    margin-left: 250px;
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

.greeting-link {
    margin-top: 1rem;
    padding: 1rem;
}

.greeting-button {
    display: inline-block;
    padding: 0.5rem 1rem;
    background: var(--primary-color, #2c3e50);
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s ease;
}

.greeting-button:hover {
    background: var(--primary-color-dark, #1a2632);
}
</style>
