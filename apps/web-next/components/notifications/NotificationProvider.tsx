"use client";

import Link from "next/link";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode
} from "react";

type NotificationInput = {
  title: string;
  message: string;
  tone?: "success" | "info" | "error";
  action?: {
    label: string;
    href: string;
  };
  dismissLabel?: string;
  duration?: number;
};

type ActiveNotification = NotificationInput & { id: number };

type NotificationContextValue = {
  notify: (notification: NotificationInput) => void;
  dismiss: () => void;
};

const NotificationContext = createContext<NotificationContextValue | null>(null);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notification, setNotification] = useState<ActiveNotification | null>(null);
  const nextId = useRef(0);

  const dismiss = useCallback(() => setNotification(null), []);
  const notify = useCallback((input: NotificationInput) => {
    nextId.current += 1;
    setNotification({ ...input, id: nextId.current });
  }, []);

  useEffect(() => {
    if (!notification) {
      return undefined;
    }

    const timeout = window.setTimeout(dismiss, notification.duration ?? 5500);
    return () => window.clearTimeout(timeout);
  }, [dismiss, notification]);

  useEffect(() => {
    if (!notification) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        dismiss();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [dismiss, notification]);

  const value = useMemo(() => ({ notify, dismiss }), [dismiss, notify]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <div className="mw-notification-region" aria-live="polite" aria-atomic="true">
        {notification ? (
          <aside
            className={`mw-notification mw-notification--${notification.tone ?? "info"}`}
            aria-label={notification.title}
            key={notification.id}
          >
            <div className="mw-notification__content">
              <p className="mw-notification__title">{notification.title}</p>
              <p>{notification.message}</p>
            </div>
            <div className="mw-notification__actions">
              {notification.dismissLabel ? (
                <button type="button" onClick={dismiss}>
                  {notification.dismissLabel}
                </button>
              ) : null}
              {notification.action ? (
                <Link href={notification.action.href} onClick={dismiss}>
                  {notification.action.label}
                </Link>
              ) : null}
            </div>
            <button
              className="mw-notification__close"
              type="button"
              onClick={dismiss}
              aria-label="Cerrar notificación"
            >
              ×
            </button>
          </aside>
        ) : null}
      </div>
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotification must be used within NotificationProvider.");
  }

  return context;
}
