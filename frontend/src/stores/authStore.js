import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
getAuth, 
signInWithEmailAndPassword,
signOut,
onAuthStateChanged 
} from 'firebase/auth'

export const useAuthStore = defineStore('auth', () => {
// State
const user = ref(null)
const loading = ref(true)
const error = ref(null)

// Getters
const isAuthenticated = computed(() => !!user.value)
const currentUser = computed(() => user.value)
const isLoading = computed(() => loading.value)
const authError = computed(() => error.value)
const userToken = computed(async () => {
    if (!user.value) return null
    return await user.value.getIdToken()
})

// Actions
async function login(email, password) {
    loading.value = true
    error.value = null
    try {
    const auth = getAuth()
    const userCredential = await signInWithEmailAndPassword(auth, email, password)
    user.value = userCredential.user
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    loading.value = false
    }
}

async function logout() {
    loading.value = true
    error.value = null
    try {
    const auth = getAuth()
    await signOut(auth)
    user.value = null
    } catch (err) {
    error.value = err.message
    throw err
    } finally {
    loading.value = false
    }
}

function initializeAuthListener() {
    const auth = getAuth()
    onAuthStateChanged(auth, (firebaseUser) => {
    loading.value = true
    try {
        if (firebaseUser) {
        user.value = firebaseUser
        } else {
        user.value = null
        }
    } catch (err) {
        error.value = err.message
    } finally {
        loading.value = false
    }
    })
}

// Reset store state
function resetState() {
    user.value = null
    loading.value = false
    error.value = null
}

return {
    // State
    user,
    loading,
    error,
    
    // Getters
    isAuthenticated,
    currentUser,
    isLoading,
    authError,
    userToken,
    
    // Actions
    login,
    logout,
    initializeAuthListener,
    resetState
}
})

