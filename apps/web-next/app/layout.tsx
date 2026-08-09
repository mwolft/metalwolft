import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { BackToTopButton } from "@/components/layout/BackToTopButton";
import { ScrollRestoration } from "@/components/layout/ScrollRestoration";
import { GtmAnalytics } from "@/components/analytics/GtmAnalytics";
import { CookieConsentBanner } from "@/components/analytics/CookieConsentBanner";
import { CartProvider } from "@/components/cart/CartProvider";
import { NotificationProvider } from "@/components/notifications/NotificationProvider";
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

export const viewport: Viewport = {
  themeColor: "#cf1c35"
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <GtmAnalytics />
        <CookieConsentBanner />
        <ScrollRestoration />
        <CartProvider>
          <NotificationProvider>
            <div className="mw-site-shell">
              <SiteHeader />
              <main className="mw-site-main">{children}</main>
              <SiteFooter />
              <BackToTopButton />
            </div>
          </NotificationProvider>
        </CartProvider>
      </body>
    </html>
  );
}
