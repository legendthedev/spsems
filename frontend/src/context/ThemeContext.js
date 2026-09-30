import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const getInitialPreference = () => {
    try {
      const saved = localStorage.getItem('spsems_theme_pref');
      if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
    } catch {
      // fallback
    }
    return 'system';
  };

  const getInitialPromptStatus = () => {
    try {
      return localStorage.getItem('spsems_theme_chosen') !== 'true';
    } catch {
      return false;
    }
  };

  const [themePreference, setThemePreference] = useState(getInitialPreference);
  const [showPrompt, setShowPrompt] = useState(getInitialPromptStatus);
  const [systemIsDark, setSystemIsDark] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return true;
  });

  const resolvedTheme = themePreference === 'system'
    ? (systemIsDark ? 'dark' : 'light')
    : themePreference;

  // Sync resolved theme with DOM attributes
  const applyThemeToDom = useCallback((theme) => {
    if (typeof document === 'undefined') return;
    document.documentElement.setAttribute('data-theme', theme);

    const metaColorScheme = document.querySelector('meta[name="color-scheme"]');
    if (metaColorScheme) {
      metaColorScheme.setAttribute('content', theme);
    }

    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme === 'dark' ? '#0a0a0a' : '#16a34a');
    }
  }, []);

  useEffect(() => {
    applyThemeToDom(resolvedTheme);
  }, [resolvedTheme, applyThemeToDom]);

  // Listen to OS / device setting changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      setSystemIsDark(e.matches);
    };

    // Modern API with fallback
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  const selectPreference = useCallback((pref) => {
    if (pref !== 'system' && pref !== 'light' && pref !== 'dark') return;
    setThemePreference(pref);
    try {
      localStorage.setItem('spsems_theme_pref', pref);
    } catch {}
  }, []);

  const confirmTheme = useCallback((pref) => {
    const chosen = pref || themePreference;
    selectPreference(chosen);
    setShowPrompt(false);
    try {
      localStorage.setItem('spsems_theme_chosen', 'true');
    } catch {}
  }, [selectPreference, themePreference]);

  const dismissPrompt = useCallback(() => {
    setShowPrompt(false);
    try {
      localStorage.setItem('spsems_theme_chosen', 'true');
    } catch {}
  }, []);

  const openPrompt = useCallback(() => {
    setShowPrompt(true);
  }, []);

  const toggleTheme = useCallback(() => {
    if (themePreference === 'system') {
      selectPreference('light');
    } else if (themePreference === 'light') {
      selectPreference('dark');
    } else {
      selectPreference('system');
    }
  }, [themePreference, selectPreference]);

  return (
    <ThemeContext.Provider
      value={{
        themePreference,
        resolvedTheme,
        systemIsDark,
        showPrompt,
        selectPreference,
        confirmTheme,
        dismissPrompt,
        openPrompt,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
