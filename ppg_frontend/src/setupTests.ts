import '@testing-library/jest-dom';

// Global mocks or test setup can go here. For example, if you want to mock
// window.matchMedia or other browser APIs used by MUI components.

if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

// TextEncoder/TextDecoder polyfill for Jest/node environment
// eslint-disable-next-line @typescript-eslint/no-var-requires
const _util = require('util');
if (typeof globalThis.TextEncoder === 'undefined') {
  // In Jest/node env use the util exports as polyfill
  // Assign on globalThis to support both browser-like and node-like globals
  // @ts-ignore - runtime assignment of globals declared in src/global.d.ts
  globalThis.TextEncoder = _util.TextEncoder;
  // @ts-ignore - runtime assignment of globals declared in src/global.d.ts
  globalThis.TextDecoder = _util.TextDecoder;
}
