<script setup>
import { ref, onMounted } from 'vue';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import axios from "axios";

const error = ref('');
const loading = ref(false);
const auth = getAuth();

const emit = defineEmits(['login-success', 'login-error']);

onMounted(() => {
    // Clear any existing auth state on component mount
    auth.signOut().catch(e => {
        console.error('Error clearing auth state:', e);
    });
});
const handleGoogleLogin = async () => {
    if (loading.value) return;
    
    error.value = '';
    loading.value = true;
    
    try {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        const token = await result.user.getIdToken();
        
        // Create or update user in backend
        await axios.post("http://127.0.0.1:8000/api/users", 
            {
                id: result.user.uid,
                email: result.user.email,
                name: result.user.displayName,
            },
            {
                headers: { Authorization: `Bearer ${token}` },
            }
        );
        
        emit('login-success', { 
            uid: result.user.uid,
            email: result.user.email,
            displayName: result.user.displayName,
            token
        });
        
    } catch (e) {
        console.error('Login error:', e);
        error.value = e.response?.data?.message || e.message || 'Failed to login. Please try again.';
        emit('login-error', error.value);
        
        // Clear auth state on error
        auth.signOut().catch(console.error);
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <div class="login-container">
        <div class="login-box">
            <h2>Login</h2>

            <button type="button" @click="handleGoogleLogin" :disabled="loading" class="google-button">
                {{ loading ? 'Logging in...' : 'Login with Google' }}
            </button>
        </div>
    </div>
</template>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
    background-color: #f5f5f5;
}

.login-box {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

h2 {
    margin-bottom: 1.5rem;
    color: #333;
    text-align: center;
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

label {
    color: #666;
    font-size: 0.9rem;
}

input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    transition: border-color 0.3s;
}

input:focus {
    outline: none;
    border-color: #4a90e2;
}

input:disabled {
    background-color: #f5f5f5;
    cursor: not-allowed;
}

.login-button {
    background-color: #4a90e2;
    color: white;
    padding: 0.75rem;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s;
}

.login-button:hover:not(:disabled) {
    background-color: #357abd;
}

.login-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.error-message {
    color: #dc3545;
    font-size: 0.9rem;
    margin-top: 0.5rem;
    text-align: center;
}

.divider {
    margin: 1rem 0;
    text-align: center;
    position: relative;
}

.divider::before,
.divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 45%;
    height: 1px;
    background-color: #ddd;
}

.divider::before {
    left: 0;
}

.divider::after {
    right: 0;
}

.google-button {
    background-color: #4285f4;
    color: white;
    padding: 0.75rem;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    width: 100%;
    transition: background-color 0.3s;
}

.google-button:hover:not(:disabled) {
    background-color: #357abd;
}

.google-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}
</style>
