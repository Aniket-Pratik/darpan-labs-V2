'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

interface SideSwitcherProps {
  side: 'create' | 'brand';
}

export function SideSwitcher({ side }: SideSwitcherProps) {
  if (side === 'create') {
    return (
      <Link
        href="/brand/experiments"
        className="flex items-center gap-1.5 text-sm text-darpan-cyan/70 hover:text-darpan-cyan transition-colors"
      >
        I am a Brand
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    );
  }

  return (
    <Link
      href="/create/modules"
      className="flex items-center gap-1.5 text-sm text-darpan-lime/70 hover:text-darpan-lime transition-colors"
    >
      Create My Twin
      <ArrowRight className="w-3.5 h-3.5" />
    </Link>
  );
}
