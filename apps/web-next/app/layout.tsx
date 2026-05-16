import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { siteConfig } from "@/lib/metadata";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.siteUrl),
  title: {
    default: siteConfig.defaultTitle,
    template: "%s | MetalWolft"
  },
  description: siteConfig.defaultDescription,
  openGraph: {
    siteName: siteConfig.name,
    locale: "es_ES",
    type: "website"
  }
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <div className="mw-site-shell">
          <SiteHeader />
          <main className="mw-site-main">{children}</main>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
