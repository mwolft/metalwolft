import type { PropsWithChildren } from "react";

export function PageContainer({ children }: PropsWithChildren) {
  return <div className="mw-container">{children}</div>;
}
