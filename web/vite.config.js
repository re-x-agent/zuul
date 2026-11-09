import { defineConfig } from 'vite'
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  return {
    base: process.env.PUBLIC_URL ? process.env.PUBLIC_URL : '/',
    envPrefix: 'REACT_APP',
    test: {
      globals: true,
      environment: 'jsdom',
    },
    resolve: {
      alias: {
        'store': mode === 'production'
        // eslint-disable-next-line no-undef
          ? path.resolve(__dirname, './src/store.prod')
        // eslint-disable-next-line no-undef
          : path.resolve(__dirname, './src/store.dev')
      }
    },
  }
})
