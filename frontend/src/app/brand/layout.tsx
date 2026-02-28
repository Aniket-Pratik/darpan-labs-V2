import { Navbar } from '@/components/navigation';

export default function BrandLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar side="brand" />
      <main className="flex-1">{children}</main>
    </div>
  );
}
