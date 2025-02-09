import { defineStore } from 'pinia'
import { getAuth } from 'firebase/auth'
import axios from 'axios'

export const useCategoryStore = defineStore('category', {
state: () => ({
    categories: [],
    categoryGroups: [],
    loading: false,
    error: null
}),

getters: {
    filteredCategories: (state) => {
    return state.categories.filter(category => !category.is_income)
    },
    categoriesByGroup: (state) => {
    const grouped = {}
    state.categoryGroups.forEach(group => {
        grouped[group.id] = state.categories.filter(
        category => category.category_group_id === group.id
        )
    })
    return grouped
    }
},

actions: {
    async fetchCategories() {
    this.loading = true
    this.error = null
    try {
        const auth = getAuth()
        const user = auth.currentUser
        
        if (!user) {
        throw new Error('User not authenticated')
        }

        const token = await user.getIdToken()
        const response = await axios.get('/api/categories', {
        headers: {
            Authorization: `Bearer ${token}`
        }
        })
        
        this.categories = response.data.categories
        this.categoryGroups = response.data.category_groups
    } catch (error) {
        this.error = error.message
        console.error('Error fetching categories:', error)
    } finally {
        this.loading = false
    }
    },

    async createCategoryGroup(name) {
    this.loading = true
    this.error = null
    try {
        const auth = getAuth()
        const user = auth.currentUser
        
        if (!user) {
        throw new Error('User not authenticated')
        }

        const token = await user.getIdToken()
        const response = await axios.post('/api/category_groups', 
        { name },
        {
            headers: {
            Authorization: `Bearer ${token}`
            }
        }
        )
        
        this.categoryGroups.push(response.data)
        return response.data
    } catch (error) {
        this.error = error.message
        console.error('Error creating category group:', error)
        throw error
    } finally {
        this.loading = false
    }
    },

    async updateCategoryValue(categoryId, updates) {
    this.loading = true
    this.error = null
    try {
        const auth = getAuth()
        const user = auth.currentUser
        
        if (!user) {
        throw new Error('User not authenticated')
        }

        const token = await user.getIdToken()
        const response = await axios.put(
        `/api/categories/${categoryId}`,
        updates,
        {
            headers: {
            Authorization: `Bearer ${token}`
            }
        }
        )

        const index = this.categories.findIndex(c => c.id === categoryId)
        if (index !== -1) {
        this.categories[index] = response.data
        }

        return response.data
    } catch (error) {
        this.error = error.message
        console.error('Error updating category:', error)
        throw error
    } finally {
        this.loading = false
    }
    },

    async addCategory(categoryData) {
    this.loading = true
    this.error = null
    try {
        const auth = getAuth()
        const user = auth.currentUser
        
        if (!user) {
        throw new Error('User not authenticated')
        }

        const token = await user.getIdToken()
        const response = await axios.post(
        '/api/categories',
        categoryData,
        {
            headers: {
            Authorization: `Bearer ${token}`
            }
        }
        )

        this.categories.push(response.data)
        return response.data
    } catch (error) {
        this.error = error.message
        console.error('Error adding category:', error)
        throw error
    } finally {
        this.loading = false
    }
    }
}
})

