module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react-hooks/recommended",
  ],
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ["@typescript-eslint"],
  rules: {},
  settings: {
    react: {
      version: "detect",
    },
  },
  overrides: [
    {
      files: ["vite.config.ts", "vite.config.js", "vite.config.mjs"],
      env: {
        node: true,
      },
    },
  ],
};