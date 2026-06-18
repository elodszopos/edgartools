import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['node_modules'] },
  js.configs.recommended,
  tseslint.configs.recommended,
  {
    // orval mechanically escapes '/' inside .describe() string literals
    files: ['src/generated/**'],
    rules: { 'no-useless-escape': 'off' },
  },
);
