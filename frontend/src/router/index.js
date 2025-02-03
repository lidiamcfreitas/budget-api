import { createRouter, createWebHistory } from 'vue-router'
import { getAuth } from 'firebase/auth'
import { useBudgetStore } from '../stores/budgetStore'

import Login from '../components/Login.vue'
import Dashboard from '../components/Dashboard.vue'
import BudgetCreate from '../components/BudgetCreate.vue'
import SelectBudget from '../components/SelectBudget.vue'

const routes = [
{
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false, requiresBudget: false }
},
{
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, requiresBudget: true }
},
{
    path: '/create-budget',
    name: 'BudgetCreate',
    component: BudgetCreate,
    meta: { requiresAuth: true, requiresBudget: false }
},
{
    path: '/select-budget',
    name: 'SelectBudget',
    component: SelectBudget,
    meta: { requiresAuth: true, requiresBudget: false, isSelectBudget: true }
}
]

const router = createRouter({
history: createWebHistory(),
routes
})

router.beforeEach(async (to, from, next) => {
    const auth = getAuth()
    const budgetStore = useBudgetStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
    const requiresBudget = to.matched.some(record => record.meta.requiresBudget !== false)
    const isAuthenticated = auth.currentUser
    const isSelectBudgetRoute = to.matched.some(record => record.meta.isSelectBudget)

    if (requiresAuth && !isAuthenticated) {
        next('/login')
        return
    }

    if (to.path === '/login' && isAuthenticated) {
        next('/')
        return
    }

    // Load budgets if authenticated and they haven't been loaded
    if (isAuthenticated && !budgetStore.loaded) {
        try {
            await budgetStore.fetchBudgets()
        } catch (error) {
            console.error('Error loading budgets:', error)
            // Consider redirecting to an error page if budget loading fails
        }
    }

    // Budget requirement checks
    if (isAuthenticated && !isSelectBudgetRoute) {
        const hasSelectedBudget = budgetStore.selectedBudgetId
        const hasBudgets = budgetStore.budgets.length > 0

        if (!hasBudgets && requiresBudget) {
            next('/create-budget')
            return
        }

        if (!hasSelectedBudget && requiresBudget) {
            next('/select-budget')
            return
        }
    }

    next()
})

export default router