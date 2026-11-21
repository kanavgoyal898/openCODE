import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "openCODE clone explorer",
  description: "Evidence-based code clone analysis",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
