import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './authStore'

export const usePayeeStore = defineStore('payee', () => {
// State
const payees = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedPayee = ref(null)
const searchQuery = ref('')
const filterMerchantType = ref(null)

// Auth store
const authStore = useAuthStore()

// API base configuration
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL
})

// Request interceptor for API calls
api.interceptors.request.use(
    (config) => {
    config.headers.Authorization = `Bearer ${authStore.token}`
    return config
    },
    (error) => {
    return Promise.reject(error)
    }
)

// Actions
const fetchPayees = async () => {
    isLoading.value = true
    error.value = null
    try {
    const response = await api.get('/api/payees')
    payees.value = response.data
    } catch (err) {
    error.value = err.message
    } finally {
    isLoading.value = false
    }
}

const createPayee = async (payeeData) => {
    isLoading.value = true
    error.value = null
    try {
    const response = await api.post('/api/payees', payeeData)
    payees.value.push(response.data)
    return response.data
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    isLoading.value = false
    }
}

const updatePayee = async (payeeId, payeeData) => {
    isLoading.value = true
    error.value = null
    try {
    const response = await api.put(`/api/payees/${payeeId}`, payeeData)
    const index = payees.value.findIndex(p => p.payee_id === payeeId)
    if (index !== -1) {
        payees.value[index] = response.data
    }
    return response.data
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    isLoading.value = false
    }
}

const deletePayee = async (payeeId) => {
    isLoading.value = true
    error.value = null
    try {
    await api.delete(`/api/payees/${payeeId}`)
    payees.value = payees.value.filter(p => p.payee_id !== payeeId)
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    isLoading.value = false
    }
}

const updatePayeeAlias = async (payeeId, aliases) => {
    isLoading.value = true
    error.value = null
    try {
    const response = await api.put(`/api/payees/${payeeId}/aliases`, { aliases })
    const index = payees.value.findIndex(p => p.payee_id === payeeId)
    if (index !== -1) {
        payees.value[index].imported_aliases = response.data.imported_aliases
    }
    return response.data
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    isLoading.value = false
    }
}

const updateLastUsed = async (payeeId) => {
    const index = payees.value.findIndex(p => p.payee_id === payeeId)
    if (index !== -1) {
    payees.value[index].last_used = new Date().toISOString()
    }
}

// Computed properties
const sortedPayees = computed(() => {
    return [...payees.value].sort((a, b) => {
    // Sort by last used (most recent first)
    return new Date(b.last_used || 0) - new Date(a.last_used || 0)
    })
})

const payeesByMerchantType = computed(() => {
    return payees.value.reduce((acc, payee) => {
    const type = payee.merchant_type || 'uncategorized'
    if (!acc[type]) {
        acc[type] = []
    }
    acc[type].push(payee)
    return acc
    }, {})
})

const suggestedCategories = computed(() => (payeeId) => {
const payee = payees.value.find(p => p.payee_id === payeeId)
if (!payee || !payee.transactions) return []

// Count categories used with this payee
const categoryCount = payee.transactions.reduce((acc, transaction) => {
    if (transaction.category_id) {
    acc[transaction.category_id] = (acc[transaction.category_id] || 0) + 1
    }
    return acc
}, {})

// Sort by frequency and return top 3
return Object.entries(categoryCount)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 3)
    .map(([categoryId]) => categoryId)
})

const filteredPayees = computed(() => {
let result = payees.value

// Filter by search query
if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(payee => 
    payee.name.toLowerCase().includes(query) ||
    (payee.imported_aliases && payee.imported_aliases.some(alias => 
        alias.toLowerCase().includes(query)
    ))
    )
}

// Filter by merchant type
if (filterMerchantType.value) {
    result = result.filter(payee => 
    payee.merchant_type === filterMerchantType.value
    )
}

return result
})

const payeeMetrics = computed(() => {
const total = payees.value.length
const byMerchantType = payeesByMerchantType.value
const activeLastMonth = payees.value.filter(p => {
    const lastUsed = new Date(p.last_used || 0)
    const oneMonthAgo = new Date()
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1)
    return lastUsed > oneMonthAgo
}).length

return {
    total,
    byMerchantType: Object.fromEntries(
    Object.entries(byMerchantType).map(([type, items]) => 
        [type, items.length]
    )
    ),
    activeLastMonth
}
})

const getPayeeByAlias = computed(() => {
    return (alias) => {
    return payees.value.find(p => 
        p.imported_aliases && p.imported_aliases.includes(alias)
    )
    }
})

return {
    // State
    payees,
    isLoading,
    error,
    selectedPayee,
    searchQuery,
    filterMerchantType,

    // Actions
    fetchPayees,
    createPayee,
    updatePayee,
    deletePayee,
    updatePayeeAlias,
    updateLastUsed,

    // Computed
    sortedPayees,
    payeesByMerchantType,
    getPayeeByAlias,
    filteredPayees,
    suggestedCategories,
    payeeMetrics
}
})

