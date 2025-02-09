import { defineStore } from 'pinia'
import { auth } from '@/firebase'
import { useAccountStore } from './accountStore'
import { useCategoryStore } from './categoryStore'
import axios from 'axios'

export const useTransactionStore = defineStore('transactions', {
state: () => ({
    transactions: [],
    recurringTransactions: [],
    isLoading: false,
    isSubmitting: false,
    error: null,
    filters: {
    startDate: null,
    endDate: null,
    accountId: null,
    categoryId: null,
    cleared: null,
    search: ''
    },
    sortBy: {
    field: 'date',
    direction: 'desc'
    }
}),

getters: {
    // Get filtered and sorted transactions
    filteredTransactions: (state) => {
    let filtered = [...state.transactions]

    if (state.filters.startDate) {
        filtered = filtered.filter(t => new Date(t.date) >= new Date(state.filters.startDate))
    }
    if (state.filters.endDate) {
        filtered = filtered.filter(t => new Date(t.date) <= new Date(state.filters.endDate))
    }
    if (state.filters.accountId) {
        filtered = filtered.filter(t => t.account_id === state.filters.accountId)
    }
    if (state.filters.categoryId) {
        filtered = filtered.filter(t => t.category_id === state.filters.categoryId)
    }
    if (state.filters.cleared !== null) {
        filtered = filtered.filter(t => t.cleared === state.filters.cleared)
    }
    if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(t => 
        t.description.toLowerCase().includes(search) || 
        t.notes?.toLowerCase().includes(search)
        )
    }

    // Sort transactions
    filtered.sort((a, b) => {
        const aVal = a[state.sortBy.field]
        const bVal = b[state.sortBy.field]
        const modifier = state.sortBy.direction === 'desc' ? -1 : 1

        if (state.sortBy.field === 'date') {
        return modifier * (new Date(aVal) - new Date(bVal))
        }
        return modifier * (aVal > bVal ? 1 : -1)
    })

    return filtered
    },

    // Get transactions by account
    transactionsByAccount: (state) => (accountId) => {
    return state.transactions.filter(t => t.account_id === accountId)
    },

    // Get recurring transactions
    activeRecurringTransactions: (state) => {
    return state.recurringTransactions.filter(t => t.active)
    }
},

actions: {
    // Fetch all transactions
    async fetchTransactions() {
    if (!auth.currentUser) return
    
    this.isLoading = true
    this.error = null

    try {
        const response = await axios.get('/api/transactions', {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })
        this.transactions = response.data
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to fetch transactions'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    // Create a new transaction
    async createTransaction(transactionData) {
    if (!auth.currentUser) return

    this.isSubmitting = true
    this.error = null
    const accountStore = useAccountStore()

    try {
        const response = await axios.post('/api/transactions', transactionData, {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })
        
        this.transactions.push(response.data)
        // Update account balance
        await accountStore.updateAccountBalance(transactionData.account_id)
        
        return response.data
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to create transaction'
        throw error
    } finally {
        this.isSubmitting = false
    }
    },

    // Update a transaction
    async updateTransaction(id, updateData) {
    if (!auth.currentUser) return

    this.isSubmitting = true
    this.error = null
    const accountStore = useAccountStore()

    try {
        const response = await axios.put(`/api/transactions/${id}`, updateData, {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })

        const index = this.transactions.findIndex(t => t.id === id)
        if (index !== -1) {
        this.transactions[index] = response.data
        }

        // Update account balance if amount changed
        await accountStore.updateAccountBalance(response.data.account_id)
        
        return response.data
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to update transaction'
        throw error
    } finally {
        this.isSubmitting = false
    }
    },

    // Delete a transaction
    async deleteTransaction(id) {
    if (!auth.currentUser) return

    this.isSubmitting = true
    this.error = null
    const accountStore = useAccountStore()
    const transaction = this.transactions.find(t => t.id === id)

    try {
        await axios.delete(`/api/transactions/${id}`, {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })

        this.transactions = this.transactions.filter(t => t.id !== id)
        
        // Update account balance
        if (transaction) {
        await accountStore.updateAccountBalance(transaction.account_id)
        }
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to delete transaction'
        throw error
    } finally {
        this.isSubmitting = false
    }
    },

    // Clear or unclear a transaction
    async toggleTransactionCleared(id) {
    const transaction = this.transactions.find(t => t.id === id)
    if (transaction) {
        await this.updateTransaction(id, { cleared: !transaction.cleared })
    }
    },

    // Categorize a transaction
    async categorizeTransaction(id, categoryId) {
    await this.updateTransaction(id, { category_id: categoryId })
    },

    // Fetch recurring transactions
    async fetchRecurringTransactions() {
    if (!auth.currentUser) return
    
    this.isLoading = true
    this.error = null

    try {
        const response = await axios.get('/api/recurring-transactions', {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })
        this.recurringTransactions = response.data
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to fetch recurring transactions'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    // Create recurring transaction
    async createRecurringTransaction(recurringData) {
    if (!auth.currentUser) return

    this.isSubmitting = true
    this.error = null

    try {
        const response = await axios.post('/api/recurring-transactions', recurringData, {
        headers: {
            Authorization: `Bearer ${await auth.currentUser.getIdToken()}`
        }
        })
        
        this.recurringTransactions.push(response.data)
        return response.data
    } catch (error) {
        this.error = error.response?.data?.message || 'Failed to create recurring transaction'
        throw error
    } finally {
        this.isSubmitting = false
    }
    },

    // Update filters
    setFilters(filters) {
    this.filters = { ...this.filters, ...filters }
    },

    // Update sort
    setSort(field, direction) {
    this.sortBy = { field, direction }
    },

    // Reset store state
    resetStore() {
    this.transactions = []
    this.recurringTransactions = []
    this.isLoading = false
    this.isSubmitting = false
    this.error = null
    this.filters = {
        startDate: null,
        endDate: null,
        accountId: null,
        categoryId: null,
        cleared: null,
        search: ''
    }
    this.sortBy = {
        field: 'date',
        direction: 'desc'
    }
    }
}
})

