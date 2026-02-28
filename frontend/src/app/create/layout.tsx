import { Navbar } from '@/components/navigation';

export default function CreateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar side="create" />
      <main className="flex-1">{children}</main>
    </div>
  );
}
