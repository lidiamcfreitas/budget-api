<template>
<div class="p-6">
    <div class="mb-6 flex justify-between items-center">
    <h1 class="text-2xl font-bold text-gray-900">Select a Budget</h1>
    <router-link
        to="/budgets/create"
        class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
        Create New Budget
    </router-link>
    </div>

    <div v-if="loading" class="flex justify-center items-center h-64">
    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>

    <div v-else-if="error" class="text-center p-6 bg-red-50 rounded-lg">
    <p class="text-red-500">{{ error }}</p>
    <button
        @click="loadBudgets"
        class="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
    >
        Try Again
    </button>
    </div>

    <div v-else-if="sortedBudgets.length === 0" class="text-center p-12 bg-gray-50 rounded-lg">
    <h3 class="text-lg font-medium text-gray-900 mb-2">No Budgets Found</h3>
    <p class="text-gray-500 mb-6">Create your first budget to get started</p>
    <router-link
        to="/budgets/create"
        class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
    >
        Create Budget
    </router-link>
    </div>

    <div
    v-else
    class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
    <div
        v-for="budget in sortedBudgets"
        :key="budget.budget_id"
        class="relative bg-white rounded-lg shadow-sm border border-gray-200 hover:border-blue-500 cursor-pointer transition-all duration-200"
        @click="selectBudget(budget.budget_id)"
    >
        <div class="p-6">
        <h3 class="text-lg font-medium text-gray-900 mb-2">
            {{ budget.name }}
        </h3>
        <div class="text-sm text-gray-500 space-y-1">
            <p>Currency: {{ budget.currency }}</p>
            <p>Created: {{ formatDate(budget.created_at) }}</p>
        </div>
        </div>
        <div
        class="absolute top-2 right-2"
        v-if="budget.budget_id === selectedBudgetId"
        >
        <span class="bg-blue-100 text-blue-800 text-xs px-2.5 py-0.5 rounded-full">
            Active
        </span>
        </div>
    </div>
    </div>
</div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useBudgetStore } from '../stores/budgetStore'

const router = useRouter()
const budgetStore = useBudgetStore()

const loading = computed(() => budgetStore.loading)
const error = computed(() => budgetStore.error)
const sortedBudgets = computed(() => budgetStore.sortedBudgets)
const selectedBudgetId = computed(() => budgetStore.selectedBudgetId)

const loadBudgets = async () => {
await budgetStore.fetchBudgets()
}

const selectBudget = async (budgetId) => {
try {
    await budgetStore.setSelectedBudget(budgetId)
    router.push('/dashboard')
} catch (err) {
    console.error('Failed to select budget:', err)
}
}

const formatDate = (date) => {
return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
})
}

onMounted(loadBudgets)
</script>

