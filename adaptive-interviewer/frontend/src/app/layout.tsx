import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Adaptive AI Interviewer — Darpan Labs",
  description:
    "Adaptive text-administered AI interview for digital-twin capture (laptop category).",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-darpan-bg font-sans antialiased">{children}</body>
    </html>
  );
}
