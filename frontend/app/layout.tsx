import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Whale-Eye Dashboard",
  description: "Real-time Ethereum Whale Monitoring",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-background text-white antialiased`}>
        <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,163,0.05),transparent_70%)] pointer-events-none"></div>
        {children}
      </body>
    </html>
  );
}
