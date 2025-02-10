<template>
<div id="app">
    <div v-if="loading" class="loading-overlay">
    <div class="spinner"></div>
    <p>Loading application...</p>
    </div>

    <div v-else class="app-container">
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
    
    <div v-else class="main-container">
        <SideMenu 
        v-if="isAuthenticated"
        :user="user"
        @logout="handleLogout"
        />
        <div class="content-wrapper">
        <Suspense>
            <template #default>
            <router-view />
            </template>
            <template #fallback>
            <div class="loading-spinner">
                <div class="spinner"></div>
            </div>
            </template>
        </Suspense>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
import { useBudgetStore } from './stores/budgetStore';
import Login from './components/Login.vue';
import SideMenu from './components/SideMenu.vue';

const router = useRouter();
const route = useRoute();
const auth = getAuth();
const budgetStore = useBudgetStore();
const currentRoute = computed(() => route.path);
const isAuthenticated = ref(false);
const user = ref(null);
const error = ref(null);
const loading = ref(true);

watch(isAuthenticated, (newValue, oldValue) => {
    console.log('Authentication state changed:', {
        from: oldValue,
        to: newValue,
        timestamp: new Date().toISOString(),
        currentRoute: route.path
    });
});
onMounted(async () => {
try {
    onAuthStateChanged(auth, async (userData) => {
    console.log('Auth state changed:', {
        timestamp: new Date().toISOString(),
        userData: userData ? {
            email: userData.email,
            uid: userData.uid,
            emailVerified: userData.emailVerified
        } : null,
        currentRoute: route.path
    });

    isAuthenticated.value = !!userData;
    user.value = userData;

    if (userData) {
        console.log('User authentication successful. Initializing store and redirecting to dashboard');
        await budgetStore.initializeStore();
        router.push('/dashboard');
    } else {
        console.log('No user authenticated. Redirecting to login page');
        router.push('/login');
    }
    loading.value = false;
    });
} catch (err) {
    console.error('Authentication error:', err);
    error.value = 'Failed to initialize application';
    loading.value = false;
}
});

const handleLoginSuccess = () => {
    console.log('Login success handler called', {
        timestamp: new Date().toISOString(),
        currentRoute: route.path
    });
    error.value = null;
};

const handleLoginError = (err) => {
error.value = err.message;
console.error('Login error:', err);
};

const handleLogout = async () => {
    console.log('Logout initiated', {
        timestamp: new Date().toISOString(),
        currentUser: user.value?.email,
        currentRoute: route.path
    });
    try {
        await signOut(auth);
        console.log('Logout successful, redirecting to login page');
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
background-color: #f0f2f5;
}

.app-container {
height: 100vh;
width: 100vw;
display: flex;
flex-direction: column;
}

.main-container {
display: flex;
flex: 1;
height: 100vh;
overflow: hidden;
}

.loading-overlay {
position: fixed;
top: 0;
left: 0;
right: 0;
bottom: 0;
background-color: rgba(255, 255, 255, 0.9);
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
z-index: 1000;
}

.content-wrapper {
flex: 1;
height: 100vh;
overflow-y: auto;
padding: 2rem;
}

.spinner {
width: 50px;
height: 50px;
border: 3px solid var(--border-color);
border-radius: 50%;
border-top-color: var(--primary-color);
animation: spin 1s linear infinite;
}

.loading-spinner {
display: flex;
justify-content: center;
align-items: center;
height: 100%;
}

@keyframes spin {
100% {
    transform: rotate(360deg);
}
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
