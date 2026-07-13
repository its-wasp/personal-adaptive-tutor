import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// React Testing Library doesn't auto-clean when globals are enabled through
// Vitest rather than Jest, so unmount between tests to keep queries scoped to
// the case under test.
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  localStorage.clear();
});

// jsdom implements neither of these, and both are used by the chat view:
// scrollIntoView for message pinning, matchMedia by Tailwind-driven layout
// checks. Stubbing them here keeps the noise out of individual tests.
window.HTMLElement.prototype.scrollIntoView = vi.fn();

window.matchMedia =
  window.matchMedia ||
  ((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
