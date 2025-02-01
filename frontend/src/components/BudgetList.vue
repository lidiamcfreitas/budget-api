<template>
<div class="budget-list">
    <h2>Budget Items</h2>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading">
    Loading budget data...
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error">
    {{ error }}
    <button @click="fetchBudgetData">Try Again</button>
    </div>

    <!-- Data Display -->
    <div v-else>
    <ul v-if="budgetItems.length">
        <li v-for="item in budgetItems" :key="item.id" class="budget-item">
        <span class="item-name">{{ item.name }}</span>
        <span class="item-amount">${{ item.amount }}</span>
        </li>
    </ul>
    <p v-else class="empty-state">No budget items found.</p>
    </div>
</div>
</template>

<script>
import { ref, onMounted } from 'vue'
import api from '../services/api'

export default {
name: 'BudgetList',
setup() {
    const budgetItems = ref([])
    const loading = ref(false)
    const error = ref(null)

    const fetchBudgetData = async () => {
    loading.value = true
    error.value = null

    try {
        const response = await api.get('/budget-items')
        budgetItems.value = response.data
    } catch (err) {
        error.value = 'Failed to load budget data. Please try again later.'
        console.error('Error fetching budget data:', err)
    } finally {
        loading.value = false
    }
    }

    onMounted(fetchBudgetData)

    return {
    budgetItems,
    loading,
    error,
    fetchBudgetData
    }
}
}
</script>

<style scoped>
.budget-list {
max-width: 800px;
margin: 0 auto;
padding: 20px;
}

h2 {
color: #2c3e50;
margin-bottom: 20px;
}

.loading, .error {
text-align: center;
padding: 20px;
background-color: #f8f9fa;
border-radius: 4px;
}

.error {
color: #dc3545;
}

.error button {
margin-top: 10px;
padding: 8px 16px;
background-color: #007bff;
color: white;
border: none;
border-radius: 4px;
cursor: pointer;
}

.error button:hover {
background-color: #0056b3;
}

.budget-item {
display: flex;
justify-content: space-between;
padding: 12px 16px;
margin-bottom: 8px;
background-color: white;
border: 1px solid #dee2e6;
border-radius: 4px;
}

.item-name {
font-weight: 500;
}

.item-amount {
color: #28a745;
font-weight: bold;
}

.empty-state {
text-align: center;
color: #6c757d;
font-style: italic;
}
</style>

