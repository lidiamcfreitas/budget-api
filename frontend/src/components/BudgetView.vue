<template>
    <div class="budget-view">
        <!-- Month Selector -->
        <div class="month-selector">
        <el-date-picker
            v-model="selectedMonth"
            type="month"
            format="MMMM YYYY"
            :clearable="false"
            @change="handleMonthChange"
        />
        </div>
        
        <!-- Filter Bar -->
        <div class="filter-bar">
        <el-input
            v-model="searchText"
            placeholder="Filter categories..."
            :prefix-icon="Search"
            class="search-input"
        />
        <div v-if="showAddGroup" class="add-group-input">
            <el-input
            v-model="newGroupName"
            placeholder="New group name..."
            @keyup.enter="createCategoryGroup"
            />
            <el-button type="text" @click="cancelAddGroup">
            <el-icon><Close /></el-icon>
            </el-button>
        </div>
        <el-button v-else type="primary" @click="showAddGroup = true">
            Add Category Group
        </el-button>
        </div>
    
        <!-- Categories Table -->
        <el-table
            v-loading="isLoading"
            :data="tableData"
            style="width: 100%"
            row-key="id"
            :tree-props="{ 
                children: 'children',
                hasChildren: (row) => row.isGroup && row.children && row.children.length > 0
            }"
            v-if="!loadError"
        >
            <el-table-column prop="name" label="Category" width="300">
                <template #default="scope">
                    <div :class="{ 
                        'group-row': scope.row.isGroup,
                        'category-row': !scope.row.isGroup 
                    }">
                        <template v-if="scope.row.isGroup">
                            <el-popover
                                v-model:visible="popoverVisibility[scope.row.id]"
                                :show-arrow="true"
                                trigger="click"
                                @show="handleEditStart(scope.row)"
                                :disabled="editingGroup?.id !== scope.row.id"
                            >
                                <template #reference>
                                    <div class="group-name-container">
                                        <div class="name-with-actions">
                                            <span class="group-name">
                                                {{ scope.row.name || 'Unnamed Group' }}
                                            </span>
                                            <el-popover
                                                v-model:visible="addCategoryPopoverVisibility[scope.row.id]"
                                                placement="right"
                                                :width="300"
                                                trigger="click"
                                                @show="handleAddCategoryStart(scope.row)"
                                            >
                                                <template #reference>
                                                    <el-button
                                                        class="add-category-btn"
                                                        :icon="Plus"
                                                        size="small"
                                                        type="text"
                                                    />
                                                </template>
                                                
                                                <template #default>
                                                    <div class="add-category-form">
                                                        <h3>Add New Category</h3>
                                                        <el-input
                                                            v-model="newCategoryName"
                                                            placeholder="Category Name"
                                                            size="default"
                                                            @keyup.enter="handleAddCategory(scope.row)"
                                                        />
                                                        <div class="form-actions">
                                                            <el-button
                                                                size="small"
                                                                @click="cancelAddCategory(scope.row)"
                                                            >
                                                                Cancel
                                                            </el-button>
                                                            <el-button
                                                                type="primary"
                                                                size="small"
                                                                @click="handleAddCategory(scope.row)"
                                                                :disabled="!newCategoryName"
                                                            >
                                                                Add
                                                            </el-button>
                                                        </div>
                                                    </div>
                                                </template>
                                            </el-popover>
                                        </div>
                                        <span v-if="isDev" class="debug-id">
                                            (ID: {{ scope.row.id }})
                                        </span>
                                    </div>
                                </template>
                                
                                <div class="edit-popover">
                                    <el-input 
                                        v-model="editedGroupName" 
                                        placeholder="Group name"
                                        size="small"
                                    />
                                    <div class="edit-actions">
                                        <el-button 
                                            type="warning" 
                                            size="small"
                                            @click="hideGroup(scope.row)"
                                            :icon="Hide"
                                        >
                                            Hide
                                        </el-button>
                                        <el-button 
                                            type="danger" 
                                            size="small"
                                            @click="deleteGroup(scope.row)"
                                            :icon="Delete"
                                        >
                                            Delete
                                        </el-button>
                                    </div>
                                    <div class="edit-controls">
                                        <el-button 
                                            size="small"
                                            @click="cancelEdit"
                                        >
                                            Cancel
                                        </el-button>
                                        <el-button 
                                            type="primary" 
                                            size="small"
                                            @click="saveGroupName(scope.row)"
                                        >
                                            Save
                                        </el-button>
                                    </div>
                                </div>
                            </el-popover>
                        </template>
                        <template v-else>
                            {{ scope.row.name }}
                        </template>
                    </div>
                </template>
            </el-table-column>
            
            <el-table-column prop="assigned" label="Assigned" width="200">
                <template #default="scope">
                    {{ formatCurrency(scope.row.isGroup ? scope.row.totalAssigned : scope.row.assigned || 0) }}
                </template>
            </el-table-column>
            
            <el-table-column prop="activity" label="Activity" width="200">
                <template #default="scope">
                    {{ formatCurrency(scope.row.isGroup ? scope.row.totalActivity : scope.row.activity || 0) }}
                </template>
            </el-table-column>
            
            <el-table-column prop="available" label="Available">
                <template #default="scope">
                    {{ formatCurrency(scope.row.isGroup ? scope.row.totalAvailable : scope.row.available || 0) }}
                </template>
            </el-table-column>
        </el-table>
    </div>
    </template>
    
    <script setup>
    import { ref, computed, watch, onMounted } from 'vue'
    import { useBudgetStore } from '../stores/budgetStore'
    import { Search, Close, Edit, Hide, Delete, Plus } from '@element-plus/icons-vue'
    import { ElMessage, ElMessageBox } from 'element-plus'
    import { storeToRefs } from 'pinia'

    const budgetStore = useBudgetStore()
    const { categoryGroups } = storeToRefs(budgetStore)
    const searchText = ref('')
    const showAddGroup = ref(false)
    const newGroupName = ref('')
    const editingGroup = ref(null)
    const editedGroupName = ref('')
    const selectedMonth = ref(new Date())
    const isLoading = ref(false)
    const loadError = ref(null)
    const popoverVisibility = ref({})
    const addCategoryPopoverVisibility = ref({})
    const newCategoryName = ref('')
    const isDev = ref(false)  // Enable debug IDs by default

    // Watch for budget ID changes
    watch(() => budgetStore.selectedBudgetId, async (newId) => {
        if (newId) {
            await loadBudgetData()
        }
    })

    // Watch for month changes
    watch(selectedMonth, async () => {
        await loadBudgetData()
    })

    onMounted(async () => {
        await loadBudgetData()
    })

    async function loadBudgetData() {
        isLoading.value = true
        loadError.value = null
        try {
            const formattedDate = formatDateToYYYYMM(selectedMonth.value)
            console.log('[BudgetView] Loading data for:', formattedDate)
            console.log('[BudgetView] Current budgetId:', budgetStore.selectedBudgetId)
            
            await budgetStore.fetchBudgetData(formattedDate)
            
            console.log('[BudgetView] Data loaded successfully')
            console.log('[BudgetView] Category Groups:', budgetStore.categoryGroups)
            console.log('[BudgetView] Monthly Budget Data:', budgetStore.monthlyBudgetData)
            
            if (!budgetStore.categoryGroups || budgetStore.categoryGroups.length === 0) {
                console.warn('[BudgetView] No category groups found after loading')
            } else {
                console.log('[BudgetView] Found', budgetStore.categoryGroups.length, 'category groups')
                budgetStore.categoryGroups.forEach(group => {
                    console.log('[BudgetView] Group:', {
                        id: group.id,
                        name: group.name,
                        categoryCount: group.categories?.length || 0,
                        totalAssigned: group.totalAssigned,
                        totalActivity: group.totalActivity,
                        totalAvailable: group.totalAvailable
                    })
                })
            }
        } catch (error) {
            console.error('[BudgetView] Error loading data:', error)
            console.error('[BudgetView] Error details:', {
                message: error.message,
                response: error.response?.data,
                status: error.response?.status
            })
            loadError.value = error.message || 'Failed to load budget data'
            ElMessage.error(loadError.value)
        } finally {
            isLoading.value = false
        }
    }

    const formatDateToYYYYMM = (date) => {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    }
    
    const filteredCategoryGroups = computed(() => {
        console.log('[BudgetView] Computing filtered groups')
        const groups = budgetStore.categoryGroups
        console.log('[BudgetView] Raw category groups:', groups)

        if (!groups || groups.length === 0) {
            console.warn('[BudgetView] No category groups found')
            return []
        }

        // Ensure popoverVisibility is initialized for all groups
        groups.forEach(group => {
            if (group && group.id && !popoverVisibility.value[group.id]) {
                popoverVisibility.value[group.id] = false
            }
        })

        if (!searchText.value) {
            console.log('[BudgetView] No search text, returning all groups:', groups)
            return groups
        }

        console.log('[BudgetView] Filtering groups with search:', searchText.value)
        const filtered = groups.filter(group => 
            (group.name && group.name.toLowerCase().includes(searchText.value.toLowerCase())) ||
            (group.categories && group.categories.some(cat => 
                cat.name && cat.name.toLowerCase().includes(searchText.value.toLowerCase())
            ))
        )
        console.log('[BudgetView] Filtered groups result:', filtered)
        return filtered
    })
    
    const handleMonthChange = async (date) => {
        console.log('[BudgetView] Month changed to:', date)
        const formattedDate = formatDateToYYYYMM(date)
        console.log('[BudgetView] Formatted date:', formattedDate)
        try {
            await budgetStore.fetchBudgetData(formattedDate)
            console.log('[BudgetView] Data fetched for new month')
        } catch (error) {
            console.error('[BudgetView] Error fetching data for new month:', error)
            ElMessage.error('Failed to load budget data for selected month')
        }
    }
    
    const createCategoryGroup = async () => {
    if (!newGroupName.value.trim()) {
        ElMessage.warning('Please enter a group name')
        return
    }
    
    try {
        await budgetStore.createCategoryGroup(newGroupName.value)
        showAddGroup.value = false
        newGroupName.value = ''
        ElMessage.success('Category group created')
    } catch (error) {
        ElMessage.error('Failed to create category group')
    }
    }
    
    const cancelAddGroup = () => {
    showAddGroup.value = false
    newGroupName.value = ''
    }

    const handleEditStart = (group) => {
    editedGroupName.value = group.name
    }

    const handleGroupClick = (group) => {
        editingGroup.value = group
        popoverVisibility.value[group.id] = true
    }

    const cancelEdit = () => {
        const currentGroupId = editingGroup.value?.id
        if (currentGroupId) {
            popoverVisibility.value[currentGroupId] = false
        }
        editingGroup.value = null
        editedGroupName.value = ''
    }

    const saveGroupName = async (group) => {
    if (!editedGroupName.value.trim()) {
        ElMessage.warning('Please enter a group name')
        return
    }

    try {
        await budgetStore.updateCategoryGroup({
        ...group,
        name: editedGroupName.value
        })
        const currentGroupId = editingGroup.value?.id
        if (currentGroupId) {
            popoverVisibility.value[currentGroupId] = false
        }
        editingGroup.value = null
        editedGroupName.value = ''
        ElMessage.success('Category group updated')
    } catch (error) {
        ElMessage.error('Failed to update category group')
    }
    }

    const hideGroup = async (group) => {
    try {
        await budgetStore.updateCategoryGroup({
        ...group,
        hidden: true
        })
        const currentGroupId = editingGroup.value?.id
        if (currentGroupId) {
            popoverVisibility.value[currentGroupId] = false
        }
        editingGroup.value = null
        ElMessage.success('Category group hidden')
    } catch (error) {
        ElMessage.error('Failed to hide category group')
    }
    }

    const deleteGroup = async (group) => {
    try {
        await ElMessageBox.confirm(
        'Are you sure you want to delete this category group?',
        'Warning',
        {
            confirmButtonText: 'Delete',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
        )

        await budgetStore.deleteCategoryGroup(group.id)
        const currentGroupId = editingGroup.value?.id
        if (currentGroupId) {
            popoverVisibility.value[currentGroupId] = false
        }
        editingGroup.value = null
        ElMessage.success('Category group deleted')
    } catch (error) {
        if (error !== 'cancel') {
        ElMessage.error('Failed to delete category group')
        }
    }
    }

    const handleAddCategoryStart = (group) => {
        newCategoryName.value = ''
    }

    const cancelAddCategory = (group) => {
        addCategoryPopoverVisibility.value[group.id] = false
        newCategoryName.value = ''
    }

    const handleAddCategory = async (group) => {
        if (!newCategoryName.value) return

        try {
            await budgetStore.addCategory({
                name: newCategoryName.value,
                group_id: group.id,
                budget_id: group.budget_id
            })
            
            addCategoryPopoverVisibility.value[group.id] = false
            newCategoryName.value = ''
        } catch (error) {
            console.error('Failed to add category:', error)
            ElMessage.error('Failed to add category')
        }
    }

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value)
    }
    const tableData = computed(() => {
    console.log('[BudgetView] Computing table data');
    console.log('[BudgetView] Filtered category groups:', filteredCategoryGroups.value);

    // Process groups and their categories into a flat structure for the table
    const processedData = [];

    filteredCategoryGroups.value.forEach(group => {
        // Add the group row
        const processedGroup = {
            id: group.group_id || group.id,
            name: group.name,
            isGroup: true,
            assigned: parseFloat(group.totalAssigned || 0),
            activity: parseFloat(group.totalActivity || 0),
            available: parseFloat(group.totalAvailable || 0),
            children: [] // This will hold the categories
        };
        
        processedData.push(processedGroup);
        
        // Process categories if they exist
        if (Array.isArray(group.categories)) {
            processedGroup.children = group.categories.map(category => ({
                id: category.category_id || category.id,
                name: category.name,
                isGroup: false,
                assigned: parseFloat(category.assigned || 0),
                activity: parseFloat(category.activity || 0),
                available: parseFloat(category.available || 0),
                group_id: group.group_id || group.id
            }));
        }
        
        console.log(`[BudgetView] Processed group:`, {
            id: processedGroup.id,
            name: processedGroup.name,
            categoriesCount: processedGroup.children.length,
            categories: processedGroup.children
        });
    });
    
    console.log('[BudgetView] Final table data:', processedData);
    return processedData;
    });
    </script>
    
    <style scoped>
    .name-with-actions {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .add-category-btn {
        opacity: 0;
        transition: opacity 0.2s;
    }

    .group-row:hover .add-category-btn {
        opacity: 1;
    }

    .add-category-form {
        padding: 8px;
    }

    .add-category-form h3 {
        margin-top: 0;
        margin-bottom: 16px;
    }

    .form-actions {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        margin-top: 16px;
    }

    .group-name-container {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .group-row {
        font-weight: bold;
        background-color: #f5f7fa;
    }

    .group-row:hover {
        cursor: pointer;
    }

    .category-row {
        font-weight: normal;
        padding-left: 20px;
    }

    .el-table {
        --el-table-row-hover-bg-color: #f5f7fa;
    }

    /* Target group rows specifically when expanded */
    :deep(.el-table__row--level-0.expanded) {
        background-color: #f5f7fa;
    }

    /* Add some padding to category rows */
    :deep(.el-table__row--level-1) td:first-child {
        padding-left: 40px;
    }
    .budget-view {
        padding-left: 300px;
        /* height: 100%; */
        /* overflow-y: auto; */
        background-color: #ffffff;
        /* border-radius: 8px; */
        /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
    }
    
    .month-selector {
    margin-bottom: 20px;
    display: flex;
    justify-content: left;
    }
    
    .filter-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    align-items: center;
    }
    
    .search-input {
    width: 300px;
    }
    
    .add-group-input {
    display: flex;
    gap: 8px;
    align-items: center;
    }
    
    .categories-list {
    padding: 20px;
    background-color: #f8f9fa;
    }

    .group-name {
    cursor: pointer;
    &:hover {
        color: var(--el-color-primary);
    }
    }

    .edit-popover {
    min-width: 250px;
    padding: 8px;
    }

    .edit-actions {
    display: flex;
    gap: 8px;
    margin: 16px 0;
    }

    .edit-controls {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 16px;
    }
    </style>
