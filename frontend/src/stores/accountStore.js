import { defineStore } from 'pinia'
import { auth } from '@/firebase'
import axios from 'axios'

export const useAccountStore = defineStore('account', {
state: () => ({
    accounts: [],
    isLoading: false,
    error: null,
    selectedAccount: null,
    accountTypes: ['checking', 'savings', 'credit_card', 'cash', 'investment'],
    currencies: ['USD', 'EUR', 'GBP', 'BRL'],
}),

getters: {
    // Get accounts filtered by type
    getAccountsByType: (state) => (type) => {
    return state.accounts.filter(account => account.type === type)
    },
    
    // Get total balance across all accounts
    totalBalance: (state) => {
    return state.accounts.reduce((total, account) => {
        // Convert credit card balances to negative for proper calculation
        const balance = account.type === 'credit_card' ? -account.balance : account.balance
        return total + balance
    }, 0)
    },

    // Get total assets (excluding credit cards)
    totalAssets: (state) => {
    return state.accounts
        .filter(account => account.type !== 'credit_card')
        .reduce((total, account) => total + account.balance, 0)
    },

    // Get total liabilities (credit cards)
    totalLiabilities: (state) => {
    return state.accounts
        .filter(account => account.type === 'credit_card')
        .reduce((total, account) => total + account.balance, 0)
    }
},

actions: {
    async fetchAccounts() {
    this.isLoading = true
    this.error = null
    
    try {
        const token = await auth.currentUser?.getIdToken()
        const response = await axios.get('/api/accounts', {
        headers: { Authorization: `Bearer ${token}` }
        })
        this.accounts = response.data
    } catch (error) {
        this.error = error.message || 'Failed to fetch accounts'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    async createAccount(accountData) {
    this.isLoading = true
    this.error = null

    try {
        const token = await auth.currentUser?.getIdToken()
        const response = await axios.post('/api/accounts', accountData, {
        headers: { Authorization: `Bearer ${token}` }
        })
        this.accounts.push(response.data)
        return response.data
    } catch (error) {
        this.error = error.message || 'Failed to create account'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    async updateAccount(accountId, accountData) {
    this.isLoading = true
    this.error = null

    try {
        const token = await auth.currentUser?.getIdToken()
        const response = await axios.put(`/api/accounts/${accountId}`, accountData, {
        headers: { Authorization: `Bearer ${token}` }
        })
        
        const index = this.accounts.findIndex(acc => acc.id === accountId)
        if (index !== -1) {
        this.accounts[index] = response.data
        }
        
        return response.data
    } catch (error) {
        this.error = error.message || 'Failed to update account'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    async deleteAccount(accountId) {
    this.isLoading = true
    this.error = null

    try {
        const token = await auth.currentUser?.getIdToken()
        await axios.delete(`/api/accounts/${accountId}`, {
        headers: { Authorization: `Bearer ${token}` }
        })
        
        this.accounts = this.accounts.filter(acc => acc.id !== accountId)
    } catch (error) {
        this.error = error.message || 'Failed to delete account'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    async updateBalance(accountId, newBalance) {
    this.isLoading = true
    this.error = null

    try {
        const token = await auth.currentUser?.getIdToken()
        const response = await axios.patch(`/api/accounts/${accountId}/balance`, {
        balance: newBalance
        }, {
        headers: { Authorization: `Bearer ${token}` }
        })
        
        const index = this.accounts.findIndex(acc => acc.id === accountId)
        if (index !== -1) {
        this.accounts[index].balance = response.data.balance
        }
        
        return response.data
    } catch (error) {
        this.error = error.message || 'Failed to update account balance'
        throw error
    } finally {
        this.isLoading = false
    }
    },

    setSelectedAccount(account) {
    this.selectedAccount = account
    },

    clearError() {
    this.error = null
    }
}
})

