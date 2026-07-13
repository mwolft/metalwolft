"use client";

import { useCallback, useEffect, useState } from "react";
import {
  clearSession,
  getStoredUser,
  getToken,
  subscribeToAuthSessionChanges,
  type AuthUser
} from "@/lib/auth-client";

type AuthSession = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isReady: boolean;
};

function readCurrentSession() {
  const token = getToken();
  const user = getStoredUser();

  return {
    user: token && user ? user : null,
    isAuthenticated: Boolean(token && user)
  };
}

export function useAuthSession() {
  const [session, setSession] = useState<AuthSession>({
    user: null,
    isAuthenticated: false,
    isReady: false
  });

  const refreshSession = useCallback(() => {
    setSession({
      ...readCurrentSession(),
      isReady: true
    });
  }, []);

  const logout = useCallback(() => {
    clearSession();
    refreshSession();
  }, [refreshSession]);

  useEffect(() => {
    refreshSession();

    const unsubscribe = subscribeToAuthSessionChanges(refreshSession);
    const handleStorage = (event: StorageEvent) => {
      if (event.key === "token" || event.key === "user" || event.key === null) {
        refreshSession();
      }
    };

    window.addEventListener("storage", handleStorage);

    return () => {
      unsubscribe();
      window.removeEventListener("storage", handleStorage);
    };
  }, [refreshSession]);

  return {
    ...session,
    logout
  };
}
