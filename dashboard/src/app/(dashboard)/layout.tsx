import AppLayout from "@/components/AppLayout";
import { Suspense } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={<div>Carregando...</div>}>
      <AppLayout>{children}</AppLayout>
    </Suspense>
  );
}
