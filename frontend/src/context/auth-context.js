import { createContext } from "react";

/**
 * Lives apart from AuthContext.jsx so that file exports a component and
 * nothing else — react-refresh can only fast-refresh a module whose exports
 * are all components, and a mixed module silently loses hot reload.
 */
export const AuthContext = createContext(null);
