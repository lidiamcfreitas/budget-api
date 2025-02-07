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

    // Category management state
    const categories = ref([])
    const categoryGroups = ref([])
    const categoryFilter = ref('')
    const categoriesLoading = ref(false)
    const categoriesError = ref(null)
    
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

// Category getters
const filteredCategories = computed(() => {
    if (!categories.value) return []
    if (!categoryFilter.value) return categories.value
    
    const searchTerm = categoryFilter.value.toLowerCase()
    return categories.value.filter(category => 
        category.name.toLowerCase().includes(searchTerm) ||
        category.group_name.toLowerCase().includes(searchTerm)
    )
})

const categoriesByGroup = computed(() => {
    if (!categories.value) return new Map()
    
    const grouped = new Map()
    categories.value.forEach(category => {
        if (!grouped.has(category.group_id)) {
            grouped.set(category.group_id, [])
        }
        grouped.get(category.group_id).push(category)
    })
    return grouped
})

// Actions
async function fetchBudgets() {
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

// Category management actions
async function fetchBudgetData(month = selectedMonth.value) {
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
        const rawGroups = response.data.category_groups || []

        // Map the category groups and their categories
        const processedGroups = rawGroups.map(group => {
            // Each group now contains its categories in the API response
            const groupCategories = group.categories || []
            console.log(`[BudgetStore] Processing categories for group ${group.name}:`, groupCategories)

            // Process categories for this group
            const processedCategories = groupCategories.map(cat => ({
                id: cat.category_id || cat.id,
                name: cat.name,
                group_id: cat.group_id || group.group_id,
                assigned: parseFloat(cat.assigned || 0),
                activity: parseFloat(cat.activity || 0),
                available: parseFloat(cat.available || 0),
                budget_id: cat.budget_id || group.budget_id
            }))

            // Calculate group totals from its categories
            const groupTotals = processedCategories.reduce((totals, cat) => ({
                assigned: totals.assigned + cat.assigned,
                activity: totals.activity + cat.activity,
                available: totals.available + cat.available
            }), { assigned: 0, activity: 0, available: 0 })

            // Return processed group with its categories and totals
            return {
                id: group.group_id,
                name: group.name,
                budget_id: group.budget_id,
                categories: processedCategories,
                categoryCount: processedCategories.length,
                totalAssigned: groupTotals.assigned,
                totalActivity: groupTotals.activity,
                totalAvailable: groupTotals.available
            }
        })

        // Update store state
        categoryGroups.value = processedGroups
        // Flatten all categories into a single array
        categories.value = processedGroups.flatMap(group => group.categories)

        console.log('[BudgetStore] Processed category groups:', processedGroups)
        console.log('[BudgetStore] Total categories processed:', categories.value.length)
    } catch (err) {
        monthlyBudgetError.value = err.response?.data?.detail || err.message
        console.error('[BudgetStore] Error fetching budget data:', err)
        throw err
    } finally {
        monthlyBudgetLoading.value = false
    }
}
async function fetchCategories() {
    if (!selectedBudgetId.value) return
    
    categoriesLoading.value = true
    categoriesError.value = null
    
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const response = await axios.get(
            `http://127.0.0.1:8000/api/budgets/${selectedBudgetId.value}/categories`,
            { headers: { Authorization: `Bearer ${token}` } }
        )
        
        categories.value = response.data
    } catch (err) {
        categoriesError.value = err.response?.data?.detail || err.message
        console.error('Error fetching categories:', err)
    } finally {
        categoriesLoading.value = false
    }
}

async function createCategoryGroup(groupName) {
    if (!selectedBudgetId.value) return
    
    categoriesLoading.value = true
    categoriesError.value = null
    
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const response = await axios.post(
            `http://127.0.0.1:8000/api/budgets/${selectedBudgetId.value}/category-groups`,
            { 
                name: groupName, 
                user_id: auth.currentUser.uid,
                budget_id: selectedBudgetId.value,
            },
            { headers: { Authorization: `Bearer ${token}` } }
        )
        
        categoryGroups.value = [...categoryGroups.value, response.data]
        return response.data
    } catch (err) {
        categoriesError.value = err.response?.data?.detail || err.message
        console.error('Error creating category group:', err)
        throw err
    } finally {
        categoriesLoading.value = false
    }
}

async function updateCategoryValue(categoryId, updates) {
    if (!selectedBudgetId.value) return
    
    categoriesLoading.value = true
    categoriesError.value = null
    
    try {
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const response = await axios.patch(
            `http://127.0.0.1:8000/api/categories/${categoryId}`,
            updates,
            { headers: { Authorization: `Bearer ${token}` } }
        )
        
        // Update the category in the local state
        const index = categories.value.findIndex(c => c.id === categoryId)
        if (index !== -1) {
            categories.value[index] = { ...categories.value[index], ...response.data }
        }
        
        return response.data
    } catch (err) {
        categoriesError.value = err.response?.data?.detail || err.message
        console.error('Error updating category:', err)
        throw err
    } finally {
        categoriesLoading.value = false
    }
}

function setFilter(filter) {
    categoryFilter.value = filter
}

async function setActiveBudget(budgetId) {
    if (!budgetId) {
        selectedBudgetId.value = null
        localStorage.removeItem('selectedBudgetId')
        monthlyBudgetData.value = null
        categories.value = []
        categoryGroups.value = []
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
        await fetchCategories()
    } catch (err) {
        console.error('Error loading budget data:', err)
        error.value = 'Failed to load budget data'
    }
}

function reset() {
    budgets.value = []
    selectedBudgetId.value = null
    loading.value = false
    error.value = null
    loaded.value = false
    localStorage.removeItem('selectedBudgetId')
    
    // Reset category state
    categories.value = []
    categoryGroups.value = []
    categoryFilter.value = ''
    categoriesLoading.value = false
    categoriesError.value = null
}

async function addCategory(categoryData) {
    try {
        console.log('[BudgetStore] Adding category with data:', categoryData);
        const auth = getAuth()
        const token = await auth.currentUser?.getIdToken()
        if (!token) throw new Error('Authentication required')

        const response = await axios.post(
            `http://127.0.0.1:8000/api/budgets/${selectedBudgetId.value}/category-groups/${categoryData.group_id}/categories`,
            {
                name: categoryData.name,
                group_id: categoryData.group_id,
            },
            { headers: { Authorization: `Bearer ${token}` } }
        )
        
        console.log('[BudgetStore] Category creation response:', response.data);
        console.log('[BudgetStore] Refreshing budget data...');
        await fetchBudgetData(selectedMonth.value)
        console.log('[BudgetStore] Budget data refreshed');
        
        return response.data
    } catch (error) {
        console.error('[BudgetStore] Error adding category:', error);
        console.error('[BudgetStore] Error details:', {
            message: error.message,
            response: error.response?.data,
            status: error.response?.status
        });
        throw error
    }
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
    categories,
    categoryGroups,
    categoryFilter,
    categoriesLoading,
    categoriesError,
    
    // Getters
    sortedBudgets,
    currentBudget,
    hasBudgets,
    isLoading,
    hasError,
    filteredCategories,
    categoriesByGroup,
    categoryTotals,
    groupTotals,
    
    // Actions
    fetchBudgets,
    setActiveBudget,
    reset,
    initializeStore,
    fetchCategories,
    fetchBudgetData,
    createCategoryGroup,
    setFilter,
    addCategory
}
})
