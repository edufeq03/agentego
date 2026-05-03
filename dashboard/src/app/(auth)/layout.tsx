export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-50 antialiased selection:bg-blue-500/30">
      {children}
    </div>
  );
}
