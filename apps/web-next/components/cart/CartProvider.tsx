"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode
} from "react";
import {
  countCartLines,
  getCart,
  subscribeToCartSnapshotChanges,
  type CartItem
} from "@/lib/cart-client";
import {
  getToken,
  subscribeToAuthSessionChanges
} from "@/lib/auth-client";

type CartContextValue = {
  items: readonly CartItem[];
  lineCount: number;
  revision: number;
};

const CartContext = createContext<CartContextValue | null>(null);

let pendingInitialHydration: { token: string; promise: Promise<CartItem[]> } | null = null;

function loadInitialCart(token: string) {
  if (pendingInitialHydration?.token === token) {
    return pendingInitialHydration.promise;
  }

  const promise = getCart(token, { publishSnapshot: false });
  pendingInitialHydration = { token, promise };
  void promise.then(resetInitialHydration, resetInitialHydration);
  return promise;
}

function resetInitialHydration() {
  pendingInitialHydration = null;
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<readonly CartItem[]>([]);
  const [revision, setRevision] = useState(0);
  const snapshotVersion = useRef(0);

  useEffect(
    () =>
      subscribeToCartSnapshotChanges((change) => {
        snapshotVersion.current += 1;
        setItems(change.items);
        if (change.reason === "mutation") {
          setRevision((current) => current + 1);
        }
      }),
    []
  );

  useEffect(() => {
    let isActive = true;

    function hydrate(token: string) {
      const versionAtStart = snapshotVersion.current;

      void loadInitialCart(token)
        .then((cartItems) => {
          if (isActive && snapshotVersion.current === versionAtStart) {
            snapshotVersion.current += 1;
            setItems(cartItems);
          }
        })
        .catch(() => {
          // The badge stays hidden when the persisted cart cannot be recovered.
        });
    }

    const token = getToken();
    if (token) {
      hydrate(token);
    }

    const unsubscribe = subscribeToAuthSessionChanges(() => {
      snapshotVersion.current += 1;
      resetInitialHydration();

      const currentToken = getToken();
      if (currentToken) {
        hydrate(currentToken);
        return;
      }

      setItems([]);
      setRevision((current) => current + 1);
    });

    return () => {
      isActive = false;
      unsubscribe();
    };
  }, []);

  const value = useMemo<CartContextValue>(
    () => ({ items, lineCount: countCartLines(items), revision }),
    [items, revision]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCartSnapshot() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCartSnapshot must be used within CartProvider.");
  }

  return context;
}
