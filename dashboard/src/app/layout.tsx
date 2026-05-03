import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AppLayout from "@/components/AppLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AtendIA Dashboard",
  description: "Dashboard para gestão do Agente Virtual",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full antialiased dark">
      <body className={`${inter.className} min-h-full`}>
        <AppLayout>
          {children}
        </AppLayout>
      </body>
    </html>
  );
}
