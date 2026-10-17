// Vitest setup — extends `expect` with jest-dom matchers and cleans up
// between tests. Loaded via vite.config.js `test.setupFiles`.
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
