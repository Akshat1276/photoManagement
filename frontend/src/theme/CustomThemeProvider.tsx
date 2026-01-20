import React, { createContext, useContext, useEffect, useMemo, useState, useCallback } from "react";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";

export type ColorMode = "light" | "dark";

interface ColorModeContextValue {
  mode: ColorMode;
  toggleColorMode: () => void;
}

const ColorModeContext = createContext<ColorModeContextValue>({
  mode: "light",
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  toggleColorMode: () => {},
});

export function useColorMode(): ColorModeContextValue {
  return useContext(ColorModeContext);
}

interface Props {
  children: React.ReactNode;
}

export function CustomThemeProvider({ children }: Props) {
  const [mode, setMode] = useState<ColorMode>("light");

  // Initialize from localStorage or system preference
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem("color-mode");
      if (stored === "light" || stored === "dark") {
        setMode(stored);
        return;
      }
    } catch {
      // ignore
    }
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      setMode("dark");
    }
  }, []);

  const toggleColorMode = useCallback(() => {
    setMode((prev) => {
      const next: ColorMode = prev === "light" ? "dark" : "light";
      try {
        window.localStorage.setItem("color-mode", next);
      } catch {
        // ignore
      }
      return next;
    });
  }, []);

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: mode === "light" ? "#2563eb" : "#60a5fa",
          },
          secondary: {
            main: mode === "light" ? "#ec4899" : "#f472b6",
          },
          background: {
            default: mode === "light" ? "#f5f5f7" : "#020617",
            paper: mode === "light" ? "#ffffff" : "#020617",
          },
        },
        typography: {
          fontFamily:
            'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          h6: {
            fontWeight: 600,
          },
          body1: {
            lineHeight: 1.6,
          },
          body2: {
            lineHeight: 1.6,
          },
        },
        shape: {
          borderRadius: 10,
        },
        components: {
          MuiCard: {
            styleOverrides: {
              root: {
                borderRadius: 14,
                boxShadow:
                  mode === "light"
                    ? "0 10px 30px rgba(15,23,42,0.08)"
                    : "0 18px 45px rgba(0,0,0,0.7)",
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: "none",
                borderRadius: 999,
                fontWeight: 500,
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backdropFilter: "blur(12px)",
              },
            },
          },
        },
      }),
    [mode]
  );

  const value = useMemo(
    () => ({
      mode,
      toggleColorMode,
    }),
    [mode, toggleColorMode]
  );

  return (
    <ColorModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}
