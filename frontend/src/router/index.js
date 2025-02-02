import { createRouter, createWebHistory } from 'vue-router'
import { getAuth } from 'firebase/auth'

import Login from '../components/Login.vue'
import Dashboard from '../components/Dashboard.vue'
import BudgetCreate from '../components/BudgetCreate.vue'
import GreetingForm from '../components/GreetingForm.vue'

const routes = [
{
    path: '/greeting',
    name: 'Greeting',
    component: GreetingForm
},
{
    path: '/login',
    name: 'Login',
    component: Login
},
{
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
},
{
    path: '/create-budget',
    name: 'BudgetCreate',
    component: BudgetCreate,
    meta: { requiresAuth: true }
}
]

const router = createRouter({
history: createWebHistory(),
routes
})

router.beforeEach(async (to, from, next) => {
const auth = getAuth()
const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
const isAuthenticated = auth.currentUser

if (requiresAuth && !isAuthenticated) {
    next('/login')
} else if (to.path === '/login' && isAuthenticated) {
    next('/')
} else {
    next()
}
})

export default router