import type { Metadata } from "next";
import { CustomerOrdersList } from "@/components/account/CustomerOrdersList";

export const metadata: Metadata = {
  title: "Mis pedidos | MetalWolft",
  description: "Consulta tus pedidos de MetalWolft desde tu área privada.",
  robots: {
    index: false,
    follow: false
  }
};

export default function CustomerOrdersPage() {
  return <CustomerOrdersList />;
}
