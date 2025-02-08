import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAuth } from 'firebase/auth'
import axios from 'axios'

export const useUserStore = defineStore('user', () => {
    // State
    const user = ref(null)
    const preferences = ref({
        theme: localStorage.getItem('theme') || 'light',
        currency: localStorage.getItem('currency') || 'USD',
        dateFormat: localStorage.getItem('dateFormat') || 'MM/DD/YYYY'
    })
    const loading = ref(false)
    const error = ref(null)
    const loaded = ref(false)

    // Getters
    const isAuthenticated = computed(() => !!user.value)
    const userProfile = computed(() => user.value)
    const isLoading = computed(() => loading.value)
    const hasError = computed(() => error.value !== null)

    // Actions
    async function fetchUserProfile() {
        loading.value = true
        error.value = null

        try {
            const auth = getAuth()
            const token = await auth.currentUser?.getIdToken()
            if (!token) throw new Error('Authentication required')

            const userId = auth.currentUser.uid
            const response = await axios.get(
                `http://127.0.0.1:8000/api/users/${userId}`,
                { headers: { Authorization: `Bearer ${token}` } }
            )

            user.value = response.data
            loaded.value = true
        } catch (err) {
            error.value = err.response?.data?.detail || err.message
            console.error('Error fetching user profile:', err)
        } finally {
            loading.value = false
        }
    }

    async function updateUserProfile(updates) {
        loading.value = true
        error.value = null

        try {
            const auth = getAuth()
            const token = await auth.currentUser?.getIdToken()
            if (!token) throw new Error('Authentication required')

            const userId = auth.currentUser.uid
            const response = await axios.patch(
                `http://127.0.0.1:8000/api/users/${userId}`,
                updates,
                { headers: { Authorization: `Bearer ${token}` } }
            )

            user.value = response.data
            return response.data
        } catch (err) {
            error.value = err.response?.data?.detail || err.message
            console.error('Error updating user profile:', err)
            throw err
        } finally {
            loading.value = false
        }
    }

    function updatePreference(key, value) {
        preferences.value[key] = value
        localStorage.setItem(key, value)
    }

    async function initializeStore() {
        if (loaded.value) return

        const auth = getAuth()
        if (auth.currentUser) {
            await fetchUserProfile()
        }
    }

    function reset() {
        user.value = null
        loading.value = false
        error.value = null
        loaded.value = false
    }

    return {
        // State
        user,
        preferences,
        loading,
        error,
        loaded,

        // Getters
        isAuthenticated,
        userProfile,
        isLoading,
        hasError,

        // Actions
        fetchUserProfile,
        updateUserProfile,
        updatePreference,
        initializeStore,
        reset
    }
})

