import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chemical Sourcing RFQ CRM",
  description: "Legal B2B chemical sourcing RFQ CRM"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
