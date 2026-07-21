import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CustomerOrderDetailView } from "@/components/account/CustomerOrderDetailView";

type CustomerOrderDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
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

export default async function CustomerOrderDetailPage({ params }: CustomerOrderDetailPageProps) {
  const resolvedParams = await params;
  const orderId = parseOrderId(resolvedParams.id);

  if (orderId === null) {
    notFound();
  }

  return <CustomerOrderDetailView orderId={orderId} />;
}
