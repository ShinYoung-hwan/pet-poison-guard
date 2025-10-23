/* eslint-disable @typescript-eslint/no-namespace */
// Ambient declarations to augment the global namespace for the test environment.
// This keeps typing narrow and avoids using `any`.

declare namespace NodeJS {
  interface Global {
    TextEncoder: typeof import('util').TextEncoder;
    TextDecoder: typeof import('util').TextDecoder;
  }
}

// Also augment the globalThis for environments that prefer it
declare var TextEncoder: typeof import('util').TextEncoder;
declare var TextDecoder: typeof import('util').TextDecoder;

export {};
