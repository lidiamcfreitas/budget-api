import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getAuth } from 'firebase/auth'
import axios from 'axios'

export const useBudgetStore = defineStore('budget', () => {
    // State
    const budgets = ref(null)
    const selectedBudgetId = ref(localStorage.getItem('selectedBudgetId') || null)
    const loading = ref(false)
    const error = ref(null)
    const loaded = ref(false)
    
    // Initialize store
    async function initializeStore() {
        if (loaded.value) return
        
        loading.value = true
        error.value = null
        
        try {
            const auth = getAuth()
            if (auth.currentUser) {
                await fetchBudgets()
            }
            loaded.value = true
        } catch (err) {
            error.value = err.message
            console.error('Failed to initialize budget store:', err)
        } finally {
            loading.value = false
        }
    }

// Watch for selected budget changes 
const watchBudgetId = watch(selectedBudgetId, (newId) => {
    if (newId) {
        const budget = budgets.value?.find(b => b && b.budget_id === newId)
        if (!budget && budgets.value) {
            error.value = 'Selected budget not found'
            selectedBudgetId.value = null
            localStorage.removeItem('selectedBudgetId')
        }
    }
})

// Getters
const sortedBudgets = computed(() => {
    if (!budgets.value) return []
    return [...budgets.value]
        .filter(budget => budget && budget.name)
        .sort((a, b) => 
            (a.name || '').toLowerCase().localeCompare((b.name || '').toLowerCase())
        )
})

const currentBudget = computed(() => 
    budgets.value?.find(budget => 
        budget && budget.budget_id === selectedBudgetId.value
    ) || null
)

const hasBudgets = computed(() => Array.isArray(budgets.value) && budgets.value.length > 0)
const isLoading = computed(() => loading.value)
const hasError = computed(() => error.value !== null)

// Actions
async function fetchBudgets() {
    loading.value = true
    error.value = null
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

    const userId = auth.currentUser.uid
    const response = await axios.get(`/api/users/${userId}/budgets`, {
        headers: { Authorization: `Bearer ${token}` }
    })
    
    budgets.value = Array.isArray(response.data) ? response.data : []
    
    // If no budget is selected and we have budgets, select the first one
    if (!selectedBudgetId.value && budgets.value.length > 0) {
        setActiveBudget(budgets.value[0].budget_id)
    }
    } catch (err) {
        error.value = err.response?.data?.detail || err.message || 'Error fetching budgets'
        console.error('Error fetching budgets:', err)
        selectedBudgetId.value = null
        localStorage.removeItem('selectedBudgetId')
    } finally {
        loading.value = false
        loaded.value = true
    }
}

function setActiveBudget(budgetId) {
    if (!budgetId) {
        selectedBudgetId.value = null
        localStorage.removeItem('selectedBudgetId')
        return
    }
    
    const budget = budgets.value?.find(b => b && b.budget_id === budgetId)
    if (!budget && budgets.value) {
        error.value = 'Invalid budget selection'
        return
    }
    
    selectedBudgetId.value = budgetId
    localStorage.setItem('selectedBudgetId', budgetId)
}

function reset() {
    budgets.value = []
    selectedBudgetId.value = null
    loading.value = false
    error.value = null
    loaded.value = false
    localStorage.removeItem('selectedBudgetId')
}

return {
    // State
    budgets,
    selectedBudgetId,
    loading,
    error,
    loaded,
    
    // Getters
    sortedBudgets,
    currentBudget,
    hasBudgets,
    isLoading,
    hasError,
    
    // Actions
    fetchBudgets,
    setActiveBudget,
    reset,
    initializeStore
}
})
