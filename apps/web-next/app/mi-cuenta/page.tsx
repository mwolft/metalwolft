import type { Metadata } from "next";
import { AccountOverview } from "@/components/account/AccountOverview";

export const metadata: Metadata = {
  title: "Mi cuenta | MetalWolft",
  description: "Accede al resumen privado de tu cuenta de MetalWolft.",
  robots: {
    index: false,
    follow: false
  }
};

export default function AccountPage() {
  return <AccountOverview />;
}
