import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: 'localhost',
    port: 5173,
    cors: true
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser'
  },
  optimizeDeps: {
    include: ['phaser', 'socket.io-client']
  }
})
