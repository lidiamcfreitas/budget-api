<template>
<div class="budget-create">
    <h1>Create New Budget</h1>
    
    <div v-if="successMessage" class="alert alert-success">
    {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="alert alert-error">
    {{ errorMessage }}
    </div>
    
    <form @submit.prevent="createBudget" class="budget-form">
    <div class="form-group">
        <label for="budgetName">Budget Name</label>
        <input
        id="budgetName"
        v-model="form.name"
        type="text"
        required
        :class="{ 'error': validationErrors.name }"
        placeholder="Enter budget name"
        >
        <span v-if="validationErrors.name" class="error-text">
        {{ validationErrors.name }}
        </span>
    </div>
    
    <div class="form-group">
        <label for="currency">Currency</label>
        <select
        id="currency"
        v-model="form.currency"
        required
        :class="{ 'error': validationErrors.currency }"
        >
        <option value="">Select a currency</option>
        <option value="USD">USD - US Dollar</option>
        <option value="EUR">EUR - Euro</option>
        <option value="GBP">GBP - British Pound</option>
        <option value="JPY">JPY - Japanese Yen</option>
        <option value="AUD">AUD - Australian Dollar</option>
        </select>
        <span v-if="validationErrors.currency" class="error-text">
        {{ validationErrors.currency }}
        </span>
    </div>
    
    <button type="submit" :disabled="isLoading" class="submit-button">
        {{ isLoading ? 'Creating...' : 'Create Budget' }}
    </button>
    </form>
</div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { collection, addDoc, serverTimestamp } from 'firebase/firestore'
import { db, auth } from '../firebase'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const validationErrors = reactive({
name: '',
currency: ''
})

const form = reactive({
name: '',
currency: ''
})

const validateForm = () => {
let isValid = true
validationErrors.name = ''
validationErrors.currency = ''

if (!form.name.trim()) {
    validationErrors.name = 'Budget name is required'
    isValid = false
}

if (!form.currency) {
    validationErrors.currency = 'Please select a currency'
    isValid = false
}

return isValid
}

const createBudget = async () => {
if (!validateForm()) return

try {
    isLoading.value = true
    errorMessage.value = ''
    
    const user = auth.currentUser
    if (!user) {
    throw new Error('You must be logged in to create a budget')
    }

    const budgetData = {
    name: form.name.trim(),
    currency: form.currency,
    userId: user.uid,
    createdAt: serverTimestamp(), // Use Firestore server timestamp
    status: 'active',
    lastUpdated: serverTimestamp() // Add last updated timestamp
    }

    // Ensure budgets collection exists and user has permission
    const budgetsRef = collection(db, 'budgets')
    await addDoc(budgetsRef, budgetData)
    
    successMessage.value = 'Budget created successfully!'
    form.name = ''
    form.currency = ''
    
    // Redirect to the budgets list after a short delay
    setTimeout(() => {
    router.push('/budgets')
    }, 2000)
    
} catch (error) {
    console.error('Budget creation error:', error)
    errorMessage.value = error.code === 'permission-denied' 
    ? 'You do not have permission to create budgets'
    : error.message || 'Failed to create budget'
} finally {
    isLoading.value = false
}
}
</script>

<style scoped>
.budget-create {
max-width: 600px;
margin: 2rem auto;
padding: 2rem;
background: white;
border-radius: 8px;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h1 {
color: #2c3e50;
margin-bottom: 2rem;
text-align: center;
}

.budget-form {
display: flex;
flex-direction: column;
gap: 1.5rem;
}

.form-group {
display: flex;
flex-direction: column;
gap: 0.5rem;
}

label {
font-weight: 600;
color: #2c3e50;
}

input, select {
padding: 0.75rem;
border: 1px solid #ddd;
border-radius: 4px;
font-size: 1rem;
}

input:focus, select:focus {
outline: none;
border-color: #3498db;
box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.error {
border-color: #e74c3c;
}

.error-text {
color: #e74c3c;
font-size: 0.875rem;
}

.submit-button {
background-color: #3498db;
color: white;
padding: 0.75rem;
border: none;
border-radius: 4px;
font-size: 1rem;
cursor: pointer;
transition: background-color 0.2s;
}

.submit-button:hover {
background-color: #2980b9;
}

.submit-button:disabled {
background-color: #95a5a6;
cursor: not-allowed;
}

.alert {
padding: 1rem;
border-radius: 4px;
margin-bottom: 1rem;
}

.alert-success {
background-color: #dff0d8;
color: #3c763d;
border: 1px solid #d6e9c6;
}

.alert-error {
background-color: #f2dede;
color: #a94442;
border: 1px solid #ebccd1;
}
</style>

