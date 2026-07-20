import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CustomerOrderDetailView } from "@/components/account/CustomerOrderDetailView";

type CustomerOrderDetailPageProps = {
  params: {
    id: string;
  };
};

export const metadata: Metadata = {
  title: "Detalle de pedido | MetalWolft",
  description: "Consulta el detalle de un pedido de tu cuenta de MetalWolft.",
  robots: {
    index: false,
    follow: false
  }
};

function parseOrderId(value: string) {
  if (!/^[1-9]\d*$/.test(value)) {
    return null;
  }

  const orderId = Number(value);
  return Number.isSafeInteger(orderId) ? orderId : null;
}

export default function CustomerOrderDetailPage({ params }: CustomerOrderDetailPageProps) {
  const orderId = parseOrderId(params.id);

  if (orderId === null) {
    notFound();
  }

  return <CustomerOrderDetailView orderId={orderId} />;
}
