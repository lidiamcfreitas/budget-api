import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
plugins: [vue()],
server: {
    port: 8080,
    host: true, // Needed for Docker
    watch: {
    usePolling: true // Better performance in Docker
    }
},
build: {
    outDir: 'dist',
    assetsDir: 'assets',
    // Generate source maps for better debugging
    sourcemap: true,
    // Optimize build size
    minify: 'esbuild',
    rollupOptions: {
    output: {
        manualChunks: {
        'vendor': ['vue']
        }
    }
    }
}
})
