import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getAuth } from 'firebase/auth'
import axios from 'axios'

export const useBudgetStore = defineStore('budget', () => {
    // State
    const budgets = ref(null)
    const selectedBudgetId = ref(localStorage.getItem('selectedBudgetId') || null)
    const selectedMonth = ref(new Date().toISOString().slice(0, 7)) // YYYY-MM format
    const loading = ref(false)
    const error = ref(null)
    const loaded = ref(false)

    // Monthly budget data
    const monthlyBudgetData = ref(null)
    const monthlyBudgetLoading = ref(false)
    const monthlyBudgetError = ref(null)
    
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

// Monthly budget getters
const categoryTotals = computed(() => {
    if (!monthlyBudgetData.value) return null
    
    const totals = {
        assigned: 0,
        activity: 0,
        available: 0
    }
    
    monthlyBudgetData.value.categories?.forEach(category => {
        totals.assigned += category.assigned || 0
        totals.activity += category.activity || 0
        totals.available += category.available || 0
    })
    
    return totals
})

const groupTotals = computed(() => {
    if (!monthlyBudgetData.value) return new Map()
    
    const totals = new Map()
    monthlyBudgetData.value.categories?.forEach(category => {
        if (!totals.has(category.group_id)) {
            totals.set(category.group_id, {
                assigned: 0,
                activity: 0,
                available: 0
            })
        }
        
        const groupTotal = totals.get(category.group_id)
        groupTotal.assigned += category.assigned || 0
        groupTotal.activity += category.activity || 0
        groupTotal.available += category.available || 0
    })
    
    return totals
})

// Actions
const fetchBudgets = async () => {
    loading.value = true
    error.value = null
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const userId = auth.currentUser.uid
        const response = await axios.get(`http://127.0.0.1:8000/api/users/${userId}/budgets`, {
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

// Budget data actions
const fetchBudgetData = async (month = selectedMonth.value) => {
    if (!selectedBudgetId.value) {
        console.warn('[BudgetStore] No budget selected')
        return
    }
    
    monthlyBudgetLoading.value = true
    monthlyBudgetError.value = null
    
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const response = await axios.get(
            `http://127.0.0.1:8000/api/budgets/${selectedBudgetId.value}/monthly-data/${month}`,
            { headers: { Authorization: `Bearer ${token}` } }
        )

        console.log('[BudgetStore] Raw API response:', response.data)

        monthlyBudgetData.value = response.data
        console.log('[BudgetStore] Monthly budget data updated:', response.data)
    } catch (err) {
        monthlyBudgetError.value = err.response?.data?.detail || err.message
        console.error('[BudgetStore] Error fetching budget data:', err)
        throw err
    } finally {
        monthlyBudgetLoading.value = false
    }
}

const setActiveBudget = async (budgetId) => {
    if (!budgetId) {
        selectedBudgetId.value = null
        localStorage.removeItem('selectedBudgetId')
        monthlyBudgetData.value = null
        return
    }
    
    const budget = budgets.value?.find(b => b && b.budget_id === budgetId)
    if (!budget && budgets.value) {
        error.value = 'Invalid budget selection'
        return
    }
    
    selectedBudgetId.value = budgetId
    localStorage.setItem('selectedBudgetId', budgetId)
    // Fetch budget data for the new budget
    try {
        await fetchBudgetData(selectedMonth.value)
    } catch (err) {
        console.error('Error loading budget data:', err)
        error.value = 'Failed to load budget data'
    }
}

const reset = () => {
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
    selectedMonth,
    loading,
    error,
    loaded,
    monthlyBudgetData,
    monthlyBudgetLoading,
    monthlyBudgetError,
    
    // Getters
    sortedBudgets,
    currentBudget,
    hasBudgets,
    isLoading,
    hasError,
    categoryTotals,
    groupTotals,
    
    // Actions
    initializeStore,
    fetchBudgets,
    fetchBudgetData,
    setActiveBudget,
    reset
}
})
