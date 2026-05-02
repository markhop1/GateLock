import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      pool: process.env.CI ? 'forks' : 'threads',
      poolOptions: process.env.CI
        ? {
            forks: {
              singleFork: true,
            },
          }
        : undefined,
      coverage: {
        provider: 'istanbul',
        reporter: ['text', 'json', 'html', 'lcov'],
        include: ['src/**/*.{ts,tsx}'],
        exclude: [
          'node_modules/',
          'dist/',
          'coverage/',
          'src/test/**',
          'src/**/__tests__/**',
          'src/**/*.{test,spec}.{ts,tsx}',
          '**/*.config.ts',
          '**/*.config.js',
          '**/*.config.cjs',
          '**/vite.config.ts',
          '**/vitest.config.ts',
        ],
      },
    },
  }),
)
