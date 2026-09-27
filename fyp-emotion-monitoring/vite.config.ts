import { defineConfig, loadEnv, type ConfigEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }: ConfigEnv) => {
    const env = loadEnv(mode, process.cwd(), '')
    const backend = env.VITE_BACKEND_ORIGIN || 'http://127.0.0.1:8000'

    return {
        plugins: [
            react(),
            tailwindcss(),
        ],
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './frontend/src'),
            },
        },
        base: '/',
        server: {
            proxy: {
                '/api': {
                    target: backend,
                    changeOrigin: true,
                },
                '/ws': {
                    target: backend,
                    ws: true,
                    changeOrigin: true,
                },
            },
        },
    }
})