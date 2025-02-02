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
        <div class="controls">
            <el-input
                v-model="searchQuery"
                placeholder="Search items..."
                prefix-icon="el-icon-search"
                class="search-input"
            />
            <el-button type="primary" @click="showAddForm = true">
                Add New Item
            </el-button>
        </div>

        <el-table
            v-if="filteredItems.length"
            :data="filteredItems"
            style="width: 100%"
            @sort-change="handleSort"
        >
            <el-table-column prop="date" label="Date" sortable />
            <el-table-column prop="description" label="Description" sortable />
            <el-table-column prop="amount" label="Amount" sortable>
                <template #default="{ row }">
                    ${{ row.amount.toFixed(2) }}
                </template>
            </el-table-column>
            <el-table-column label="Actions">
                <template #default="{ row }">
                    <el-button-group>
                        <el-button size="small" @click="startEdit(row)">
                            Edit
                        </el-button>
                        <el-button 
                            size="small" 
                            type="danger"
                            @click="deleteItem(row.id)"
                        >
                            Delete
                        </el-button>
                    </el-button-group>
                </template>
            </el-table-column>
        </el-table>
        <p v-else class="empty-state">No budget items found.</p>

        <!-- Add Form Dialog -->
        <el-dialog
            v-model="showAddForm"
            title="Add New Budget Item"
            width="500px"
        >
            <el-form :model="newItem">
                <el-form-item label="Description" required>
                    <el-input v-model="newItem.description" />
                </el-form-item>
                <el-form-item label="Amount" required>
                    <el-input-number 
                        v-model="newItem.amount"
                        :precision="2"
                        :step="0.01"
                    />
                </el-form-item>
                <el-form-item label="Date" required>
                    <el-date-picker
                        v-model="newItem.date"
                        type="date"
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="showAddForm = false">Cancel</el-button>
                <el-button type="primary" @click="addItem">
                    Create
                </el-button>
            </template>
        </el-dialog>

        <!-- Edit Form Dialog -->
        <el-dialog
            v-model="!!editingItem"
            title="Edit Budget Item"
            width="500px"
        >
            <el-form v-if="editingItem" :model="editingItem">
                <el-form-item label="Description" required>
                    <el-input v-model="editingItem.description" />
                </el-form-item>
                <el-form-item label="Amount" required>
                    <el-input-number
                        v-model="editingItem.amount"
                        :precision="2"
                        :step="0.01"
                    />
                </el-form-item>
                <el-form-item label="Date" required>
                    <el-date-picker
                        v-model="editingItem.date"
                        type="date"
                    />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="editingItem = null">Cancel</el-button>
                <el-button type="primary" @click="saveEdit">
                    Save
                </el-button>
            </template>
        </el-dialog>
    </div>
</div>
</template>

<script lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { BudgetItem, BudgetItemCreate } from '../types/budget'
import { ElMessage } from 'element-plus'

export default {
name: 'BudgetList',
setup() {
    const store = useStore()
    const budgetItems = computed(() => store.state.budget.items)
    const loading = computed(() => store.state.budget.loading)
    const error = computed(() => store.state.budget.error)
    const sortBy = ref('date')
    const sortOrder = ref('desc')
    const searchQuery = ref('')
    const showAddForm = ref(false)
    const editingItem = ref<BudgetItem | null>(null)
    
    const newItem = ref<BudgetItemCreate>({
        description: '',
        amount: 0,
        date: new Date().toISOString().split('T')[0]
    })

    const filteredItems = computed(() => {
        let items = [...budgetItems.value]
        if (searchQuery.value) {
            const query = searchQuery.value.toLowerCase()
            items = items.filter(item => 
                item.description.toLowerCase().includes(query)
            )
        }
        return items.sort((a, b) => {
            const modifier = sortOrder.value === 'desc' ? -1 : 1
            if (typeof a[sortBy.value] === 'string') {
                return modifier * a[sortBy.value].localeCompare(b[sortBy.value])
            }
            return modifier * (a[sortBy.value] - b[sortBy.value])
        })
    })

    const handleSort = ({ prop, order }) => {
        sortBy.value = prop
        sortOrder.value = order === 'descending' ? 'desc' : 'asc'
    }

    const addItem = async () => {
        try {
            await store.dispatch('budget/addItem', newItem.value)
            showAddForm.value = false
            ElMessage.success('Item added successfully')
            newItem.value = {
                description: '',
                amount: 0,
                date: new Date().toISOString().split('T')[0]
            }
        } catch (err) {
            ElMessage.error('Failed to add item')
        }
    }

    const startEdit = (item: BudgetItem) => {
        editingItem.value = { ...item }
    }

    const saveEdit = async () => {
        if (!editingItem.value) return
        try {
            await store.dispatch('budget/updateItem', editingItem.value)
            editingItem.value = null
            ElMessage.success('Item updated successfully')
        } catch (err) {
            ElMessage.error('Failed to update item')
        }
    }

    const deleteItem = async (id: string) => {
        try {
            await store.dispatch('budget/deleteItem', id)
            ElMessage.success('Item deleted successfully')
        } catch (err) {
            ElMessage.error('Failed to delete item')
        }
    }

    const fetchBudgetData = async () => {
        try {
            await store.dispatch('budget/fetchItems')
        } catch (err) {
            ElMessage.error('Failed to load budget data')
        }
    }

    onMounted(fetchBudgetData)

    return {
        budgetItems,
        loading,
        error,
        fetchBudgetData,
        filteredItems,
        searchQuery,
        showAddForm,
        newItem,
        editingItem,
        handleSort,
        addItem,
        startEdit,
        saveEdit,
        deleteItem
    }
}
</script>

<style scoped>
.budget-list {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.controls {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
}

.search-input {
    width: 300px;
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

