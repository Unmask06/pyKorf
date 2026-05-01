import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { heyApiPlugin } from '@hey-api/vite-plugin'

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
    heyApiPlugin({
      config: {
        input: '../openapi.json',
        output: 'src/api/generated',
        watch: false,
        plugins: [
          '@hey-api/typescript',
          '@hey-api/sdk',
          '@hey-api/client-axios',
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
