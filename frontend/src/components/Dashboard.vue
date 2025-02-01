<template>
<div class="dashboard">
    <header class="dashboard-header">
    <h1>Dashboard</h1>
    <button @click="handleLogout" class="logout-btn">
        Logout
    </button>
    </header>
    
    <main class="dashboard-content">
    <section class="user-profile">
        <h2>Profile Information</h2>
        <div v-if="user" class="profile-info">
        <p><strong>Email:</strong> {{ user.email }}</p>
        <p><strong>User ID:</strong> {{ user.uid }}</p>
        <p><strong>Email Verified:</strong> {{ user.emailVerified ? 'Yes' : 'No' }}</p>
        </div>
        <div v-else class="loading">
        Loading user information...
        </div>
    </section>
    </main>

    <div v-if="error" class="error-message">
    {{ error }}
    </div>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getAuth, signOut } from 'firebase/auth';
import { useRouter } from 'vue-router';

const router = useRouter();
const user = ref(null);
const error = ref(null);
const auth = getAuth();

onMounted(() => {
user.value = auth.currentUser;
auth.onAuthStateChanged((currentUser) => {
    user.value = currentUser;
    if (!currentUser) {
    router.push('/login');
    }
});
});

const handleLogout = async () => {
try {
    await signOut(auth);
    router.push('/login');
} catch (e) {
    error.value = 'Error signing out. Please try again.';
    console.error('Logout error:', e);
}
};
</script>

<style scoped>
.dashboard {
max-width: 1200px;
margin: 0 auto;
padding: 2rem;
}

.dashboard-header {
display: flex;
justify-content: space-between;
align-items: center;
margin-bottom: 2rem;
padding-bottom: 1rem;
border-bottom: 1px solid #eee;
}

.dashboard-content {
background: white;
border-radius: 8px;
padding: 2rem;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.user-profile {
max-width: 600px;
}

.profile-info {
margin-top: 1rem;
}

.profile-info p {
margin: 0.5rem 0;
padding: 0.5rem;
background: #f8f9fa;
border-radius: 4px;
}

.logout-btn {
background: #dc3545;
color: white;
border: none;
padding: 0.5rem 1rem;
border-radius: 4px;
cursor: pointer;
font-size: 1rem;
transition: background-color 0.2s;
}

.logout-btn:hover {
background: #c82333;
}

.error-message {
background: #fdecea;
color: #dc3545;
padding: 1rem;
margin-top: 1rem;
border-radius: 4px;
text-align: center;
}

.loading {
color: #666;
font-style: italic;
padding: 1rem 0;
}

@media (max-width: 768px) {
.dashboard {
    padding: 1rem;
}

.dashboard-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
}

.dashboard-content {
    padding: 1rem;
}
}
</style>

