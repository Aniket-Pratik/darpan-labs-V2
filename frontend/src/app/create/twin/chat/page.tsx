'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { ChatContainer } from '@/components/twin';

function TwinChatContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const userId = searchParams.get('userId');
  const twinId = searchParams.get('twinId') || undefined;

  const [resolvedUserId, setResolvedUserId] = useState<string | null>(userId);

  useEffect(() => {
    if (!resolvedUserId) {
      const storedUserId = localStorage.getItem('darpan_user_id');
      if (storedUserId) {
        setResolvedUserId(storedUserId);
      }
    }
  }, [resolvedUserId]);

  if (!resolvedUserId) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-4 text-center max-w-md mx-4">
          <p className="text-white/70">No user found. Please complete your interview modules first.</p>
          <button
            onClick={() => router.push('/create/modules')}
            className="px-6 py-3 bg-darpan-lime text-black font-semibold rounded-lg"
          >
            Go to Modules
          </button>
        </div>
      </div>
    );
  }

  return <ChatContainer userId={resolvedUserId} twinId={twinId} />;
}

export default function TwinChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center py-24">
          <Loader2 className="w-12 h-12 text-darpan-lime animate-spin" />
        </div>
      }
    >
      <TwinChatContent />
    </Suspense>
  );
}
