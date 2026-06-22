const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jsdom',
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    // Framework glue better covered by e2e than unit tests:
    '!app/layout.tsx', // root layout boilerplate
    '!app/api/**', // thin Next route handler proxying to the backend
  ],
  coverageThreshold: {
    global: {
      // statements/lines enforce the PRD's 70% frontend target.
      statements: 70,
      lines: 70,
      // branches/functions are regression floors below current (~66/63);
      // raising them toward 70 is a follow-up.
      branches: 60,
      functions: 60,
    },
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)