import { type ReactElement } from 'react';
import { render as rtlRender } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// If the project uses any context providers (e.g., Theme, i18n), add them here.
// Keep this file minimal: provide a custom render that wraps components with common providers.

interface RenderOptions {
  route?: string;
}

function render(ui: ReactElement, { route = '/' }: RenderOptions = {}) {
  return rtlRender(<MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>);
}

// re-export everything
export * from '@testing-library/react';
export { render };
