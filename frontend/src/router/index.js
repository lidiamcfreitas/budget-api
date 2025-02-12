import { createRouter, createWebHistory } from 'vue-router'
import { getAuth, onAuthStateChanged } from 'firebase/auth'
import { useBudgetStore } from '../stores/budgetStore'
import Login from '../components/Login.vue'
import Dashboard from '../components/Dashboard.vue'
import BudgetCreate from '../components/BudgetCreate.vue'
import SelectBudget from '../components/SelectBudget.vue'
import BudgetView from '../components/BudgetView.vue'
const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { requiresGuest: true, requiresAuth: false, requiresBudget: false }
    },
    {
        path: '/',
        name: 'Root',
        component: Dashboard,
        meta: { requiresAuth: true, requiresBudget: false }
    },
    {
        path: '/dashboard',
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
    console.log('Navigation Guard Started:', {
        to: to.path,
        from: from.path,
        meta: to.meta
    })

    const auth = getAuth()
    const currentUser = auth.currentUser

    // Log detailed auth state
    console.log('Initial Auth State:', {
        currentUser: currentUser?.email,
        uid: currentUser?.uid,
        isCurrentUserNull: currentUser === null,
        hasAuthObject: !!auth,
        destination: to.path,
        routeMeta: to.meta
    })

    // Wait for auth state to be determined
    await new Promise((resolve) => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            console.log('Auth State Changed:', {
                hasUser: !!user,
                email: user?.email,
                uid: user?.uid
            })
            unsubscribe()
            resolve(user)
        })
    })

    const isAuthenticated = auth.currentUser !== null

    console.log('Final Auth State:', {
        isAuthenticated,
        currentUser: auth.currentUser?.email,
        uid: auth.currentUser?.uid,
        path: to.path
    })

    // Handle guest-only routes (like login)
    if (to.meta.requiresGuest && isAuthenticated) {
        console.log('Redirecting to dashboard: User is authenticated')
        next('/dashboard')
        return
    }

    // Handle auth-required routes
    if (to.meta.requiresAuth && !isAuthenticated) {
        console.log('Redirecting to login: Authentication required')
        next('/login')
        return
    }

    // Handle budget requirements
    if (isAuthenticated && to.meta.requiresBudget) {
        console.log('Checking budget requirements')
        const budgetStore = useBudgetStore()
        
        if (!budgetStore.loaded) {
            console.log('Loading budgets...')
            try {
                budgetStore.fetchBudgets()
                    .then(() => {
                        const hasBudgets = budgetStore.budgets.length > 0
                        const hasSelectedBudget = budgetStore.selectedBudgetId

                        console.log('Budget state after load:', {
                            hasBudgets,
                            hasSelectedBudget,
                            budgetCount: budgetStore.budgets.length,
                            selectedId: budgetStore.selectedBudgetId
                        })

                        if (!hasBudgets) {
                            console.log('Redirecting to create-budget: No budgets found')
                            next('/create-budget')
                            return
                        }

                        if (!hasSelectedBudget && !to.meta.isSelectBudget) {
                            console.log('Redirecting to select-budget: No budget selected')
                            next('/select-budget')
                            return
                        }

                        console.log('Budget checks passed, allowing navigation')
                        next()
                    })
                    .catch(error => {
                        console.error('Error loading budgets:', error)
                        next('/create-budget')
                    })
                return
            } catch (error) {
                console.error('Error in budget fetch:', error)
                next('/create-budget')
                return
            }
        }

        const hasBudgets = budgetStore.budgets.length > 0
        const hasSelectedBudget = budgetStore.selectedBudgetId

        console.log('Budget state:', {
            hasBudgets,
            hasSelectedBudget,
            budgetCount: budgetStore.budgets.length,
            selectedId: budgetStore.selectedBudgetId
        })

        if (!hasBudgets) {
            console.log('Redirecting to create-budget: No budgets found')
            next('/create-budget')
            return
        }

        if (!hasSelectedBudget && !to.meta.isSelectBudget) {
            console.log('Redirecting to select-budget: No budget selected')
            next('/select-budget')
            return
        }
    }

    console.log('All checks passed. Allowing navigation to:', to.path)
    next()
})

export default router