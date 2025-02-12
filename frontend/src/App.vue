<template>
    <div id="app">
        <div class="app-container">
            <div class="main-container">
                <SideMenu 
                    v-if="user"
                    :user="user"
                    @logout="handleLogout"
                class="side-menu"
            />
                <div class="content-wrapper">
                    <router-view />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getAuth, onAuthStateChanged, signOut } from 'firebase/auth';
import { useBudgetStore } from './stores/budgetStore';
import SideMenu from './components/SideMenu.vue';

const auth = getAuth();
const budgetStore = useBudgetStore();
const user = ref(null);
const error = ref(null);

onMounted(() => {
    onAuthStateChanged(auth, async (userData) => {
        try {
            user.value = userData;
            
            if (userData) {
                await budgetStore.initializeStore();
            }
        } catch (err) {
            console.error('Authentication error:', err);
            error.value = 'Failed to initialize application';
        }
    });
});

const handleLogout = async () => {
    try {
        await signOut(auth);
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
    overflow-x: hidden;
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
    position: relative;
}

.side-menu {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 250px;
    z-index: 100;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.content-wrapper {
    flex: 1;
    min-height: 100vh;
    margin-left: 250px;
    padding: 2rem;
    background-color: #f0f2f5;
    overflow-y: auto;
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
    min-height: calc(100vh - 4rem);
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
