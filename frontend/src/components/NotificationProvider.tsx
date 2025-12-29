import React, { createContext, useContext, useState, ReactNode } from "react";
import { Snackbar, Alert } from "@mui/material";

type Notification = { message: string; severity?: "success" | "error" | "info" | "warning" };

type NotificationContextType = {
  notify: (message: string, severity?: Notification["severity"]) => void;
};

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [notification, setNotification] = useState<Notification>({ message: "", severity: "success" });

  const notify = (message: string, severity: Notification["severity"] = "success") => {
    setNotification({ message, severity });
    setOpen(true);
  };

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
      <Snackbar
        open={open}
        autoHideDuration={3000}
        onClose={() => setOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setOpen(false)} severity={notification.severity} sx={{ width: "100%" }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotification must be used within a NotificationProvider");
  return ctx.notify;
}
