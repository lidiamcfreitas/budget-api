import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { initializeApp } from 'firebase/app'
import { getAuth, onAuthStateChanged } from 'firebase/auth'
import App from './App.vue'
import './assets/main.css'

// Import route components
import Login from './components/Login.vue'
import Dashboard from './components/Dashboard.vue'

// Firebase configuration
const firebaseConfig = {
apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
appId: import.meta.env.VITE_FIREBASE_APP_ID
}

// Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig)
const auth = getAuth(firebaseApp)

// Router setup
const routes = [
{ path: '/login', component: Login },
{ 
    path: '/dashboard', 
    component: Dashboard,
    meta: { requiresAuth: true }
},
{ path: '/', redirect: '/login' }
]

const router = createRouter({
history: createWebHistory(),
routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
const isAuthenticated = auth.currentUser

if (requiresAuth && !isAuthenticated) {
    next('/login')
} else if (!requiresAuth && isAuthenticated) {
    next('/dashboard')
} else {
    next()
}
})

// Create Vue app
const app = createApp(App)

// Wait for Firebase auth to initialize before mounting app
onAuthStateChanged(auth, (user) => {
if (!app.__vue_app__) {
    app.use(router)
    app.mount('#app')
}
})
