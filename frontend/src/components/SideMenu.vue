<template>
<div class="side-menu">
    <div class="logo-section">
    <img src="../../data/ignite_logo_white.png" alt="Ignite Logo" class="logo-image" />
    <h1>Ignite</h1>
    <!-- <p>Numbers harmony</p> -->
    </div>
    <div class="budget-selector">
    <el-dropdown trigger="click" @command="handleBudgetSelect" :disabled="budgetStore.loading">
        <div class="current-budget" v-if="budgetStore.currentBudget">
            <span class="label">Current Budget:</span>
            <span class="value">
                {{ budgetStore.currentBudget.name }}
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
        </div>
        <template #dropdown>
            <el-dropdown-menu>
                <el-dropdown-item
                    v-for="budget in budgetStore.sortedBudgets"
                    :key="budget.budget_id"
                    :command="budget.budget_id"
                    :disabled="budget.budget_id === budgetStore.currentBudgetId"
                >
                    {{ budget.name }}
                </el-dropdown-item>
            </el-dropdown-menu>
        </template>
    </el-dropdown>
    <div v-if="budgetStore.loading" class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
    </div>
    <div v-if="error" class="error-message">
        {{ error }}
    </div>
    </div>
    <nav class="menu-items">
    <div class="menu-items-top">
        <router-link to="/" class="menu-item">
            <i class="fas fa-wallet"></i>
            <span>Budget</span>
        </router-link>
        <router-link to="/dashboard" class="menu-item">
            <i class="fas fa-chart-bar"></i>
            <span>Dashboard</span>
        </router-link>
        <router-link to="/create-budget" class="menu-item">
            <i class="fas fa-plus-circle"></i>
            <span>Create Budget</span>
        </router-link>
    </div>
    <div class="menu-items-bottom">
        <a @click="handleLogout" class="menu-item logout-btn">
            <i class="fas fa-sign-out-alt"></i>
            <span>Logout</span>
        </a>
    </div>
    </nav>
</div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useBudgetStore } from '../stores/budgetStore'
import { useAuthStore } from '../stores/authStore'
import { useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'

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

const handleBudgetSelect = async (budgetId) => {
    try {
        await budgetStore.setActiveBudget(budgetId)
        router.push('/')
    } catch (err) {
        error.value = 'Failed to switch budget'
        console.error('Error switching budget:', err)
    }
}

const navigateToCreateBudget = () => {
    router.push('/create-budget')
}

const handleLogout = async () => {
    try {
        await authStore.logout()
        router.push('/login')
    } catch (err) {
        console.error('Error logging out:', err)
    }
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
padding: 1.5rem 0;
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
    justify-content: space-between;
    height: calc(100vh - 250px); /* Adjust based on header height */
}

.menu-items-top, .menu-items-bottom {
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

.current-budget {
    cursor: pointer;
    transition: background-color 0.3s;
    padding: 1rem;
    width: 100%;
}

.current-budget:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

.el-dropdown {
    width: 100%;
}

.el-icon--right {
    margin-left: 5px;
    font-size: 12px;
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

.logout-btn {
    cursor: pointer;
    margin-bottom: 1rem;
}

.logout-btn:hover {
    background-color: rgba(255, 87, 87, 0.2);
}
</style>
