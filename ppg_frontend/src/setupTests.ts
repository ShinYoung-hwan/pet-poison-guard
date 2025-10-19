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
declare var global: any;

// eslint-disable-next-line @typescript-eslint/no-var-requires
const _util = require('util');
if (typeof global.TextEncoder === 'undefined') {
  global.TextEncoder = _util.TextEncoder;
  global.TextDecoder = _util.TextDecoder;
}
