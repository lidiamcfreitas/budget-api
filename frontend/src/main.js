import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './assets/main.css'
import { createPinia } from 'pinia'
import { initializeApp } from 'firebase/app'
import { getAuth, onAuthStateChanged } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'
import App from './App.vue'
import router from './router'

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
const db = getFirestore(firebaseApp)

// Create Vue app
const app = createApp(App)

// Create and use Pinia before router
const pinia = createPinia()
app.use(pinia)
app.use(ElementPlus)
app.use(router)

// Initialize app only after checking auth state
let appMounted = false
onAuthStateChanged(auth, (user) => {
    if (!appMounted) {
        app.mount('#app')
        appMounted = true
    }
})
