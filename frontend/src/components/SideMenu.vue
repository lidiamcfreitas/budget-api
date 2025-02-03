<template>
<div class="side-menu">
    <div class="logo-section">
    <h1>BudgetApp</h1>
    </div>
    <div class="budget-selector">
    <div class="current-budget" v-if="budgetStore.selectedBudget">
        <span class="label">Current Budget:</span>
        <span class="value">{{ budgetStore.selectedBudget.name }}</span>
    </div>
    <select
        v-model="budgetStore.selectedBudgetId"
        @change="handleBudgetSelect"
        :disabled="budgetStore.loading"
        class="budget-select"
    >
        <option value="" disabled>Select a budget</option>
        <option
        v-for="budget in budgetStore.sortedBudgets"
        :key="budget.budget_id"
        :value="budget.budget_id"
        >
        {{ budget.name }}
        </option>
    </select>
    <button
        @click="navigateToCreateBudget"
        class="create-budget-btn"
        :disabled="budgetStore.loading"
    >
        <i class="fas fa-plus"></i>
        Create New Budget
    </button>
    <div v-if="budgetStore.loading" class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
    </div>
    <div v-if="error" class="error-message">
        {{ error }}
    </div>
    </div>
    <nav class="menu-items">
    <router-link to="/" class="menu-item">
        <i class="fas fa-home"></i>
        <span>Dashboard</span>
    </router-link>
    <router-link to="/create-budget" class="menu-item">
        <i class="fas fa-plus-circle"></i>
        <span>Create Budget</span>
    </router-link>
    </nav>
</div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useBudgetStore } from '../stores/budgetStore'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'

const budgetStore = useBudgetStore()
const authStore = useAuthStore()
const router = useRouter()
const error = ref(null)

const loadBudgets = async () => {
    try {
        await budgetStore.fetchBudgets()
        error.value = null
    } catch (err) {
        error.value = 'Failed to load budgets'
        console.error('Error loading budgets:', err)
    }
}

const handleBudgetSelect = async (event) => {
    try {
        await budgetStore.setActiveBudget(event.target.value)
        router.push('/dashboard')
    } catch (err) {
        error.value = 'Failed to switch budget'
        console.error('Error switching budget:', err)
    }
}

const navigateToCreateBudget = () => {
    router.push('/create-budget')
}

watch(() => authStore.isAuthenticated, (newValue) => {
    if (newValue) {
        loadBudgets()
    } else {
        budgetStore.$reset()
    }
})

onMounted(async () => {
    if (authStore.isAuthenticated) {
        await loadBudgets()
    }
})
</script>

<style scoped>
.current-budget {
margin-bottom: 1rem;
padding: 0.5rem;
background-color: rgba(255, 255, 255, 0.1);
border-radius: 0.25rem;
}

.current-budget .label {
display: block;
font-size: 0.75rem;
color: rgba(255, 255, 255, 0.7);
margin-bottom: 0.25rem;
}

.current-budget .value {
font-weight: bold;
color: white;
}

.create-budget-btn {
width: 100%;
margin-top: 0.5rem;
padding: 0.5rem;
background-color: rgba(255, 255, 255, 0.1);
border: 1px solid rgba(255, 255, 255, 0.2);
color: white;
border-radius: 0.25rem;
cursor: pointer;
display: flex;
align-items: center;
justify-content: center;
gap: 0.5rem;
transition: background-color 0.3s;
}

.create-budget-btn:hover {
background-color: rgba(255, 255, 255, 0.2);
}

.create-budget-btn:disabled {
opacity: 0.7;
cursor: not-allowed;
}
.side-menu {
width: 250px;
height: 100vh;
background-color: #2c3e50;
color: white;
position: fixed;
left: 0;
top: 0;
padding: 1rem;
}

.logo-section {
padding: 1rem 0;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
margin-bottom: 2rem;
}

.logo-section h1 {
margin: 0;
font-size: 1.5rem;
text-align: center;
}

.menu-items {
display: flex;
flex-direction: column;
gap: 0.5rem;
}

.menu-item {
display: flex;
align-items: center;
padding: 0.75rem 1rem;
color: white;
text-decoration: none;
border-radius: 0.25rem;
transition: background-color 0.3s;
}

.menu-item:hover {
background-color: rgba(255, 255, 255, 0.1);
}

.menu-item i {
margin-right: 0.75rem;
width: 20px;
}

.menu-item.router-link-active {
background-color: rgba(255, 255, 255, 0.2);
}

.budget-selector {
padding: 1rem;
border-bottom: 1px solid rgba(255, 255, 255, 0.1);
margin-bottom: 1rem;
}

.budget-select {
width: 100%;
padding: 0.5rem;
background-color: rgba(255, 255, 255, 0.1);
color: white;
border: 1px solid rgba(255, 255, 255, 0.2);
border-radius: 0.25rem;
outline: none;
cursor: pointer;
}

.budget-select:focus {
border-color: rgba(255, 255, 255, 0.3);
}

.budget-select:disabled {
opacity: 0.7;
cursor: not-allowed;
}

.budget-select option {
background-color: #2c3e50;
color: white;
}

.loading-spinner {
text-align: center;
margin-top: 0.5rem;
color: rgba(255, 255, 255, 0.7);
}

.error-message {
color: #ff6b6b;
font-size: 0.875rem;
margin-top: 0.5rem;
text-align: center;
}
</style>

