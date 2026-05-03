import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

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
      <body className={`${inter.className} min-h-full flex`}>
        <Sidebar />
        <main className="flex-1 flex flex-col h-screen overflow-hidden">
          {/* Header/Topbar */}
          <header className="h-16 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 backdrop-blur-md flex items-center px-8 z-10">
            <h1 className="text-xl font-semibold tracking-tight text-white">Dashboard do Agente</h1>
          </header>
          
          {/* Page Content */}
          <div className="flex-1 overflow-y-auto p-8 bg-[var(--color-background)]">
            <div className="max-w-6xl mx-auto">
              {children}
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
