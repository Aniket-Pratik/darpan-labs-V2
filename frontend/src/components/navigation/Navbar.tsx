'use client';

import Link from 'next/link';
import { LayoutDashboard, Brain, MessageSquare, FlaskConical, Plus } from 'lucide-react';
import { NavItem } from './NavItem';
import { SideSwitcher } from './SideSwitcher';

const CREATE_NAV_ITEMS = [
  { label: 'Dashboard', href: '/create/dashboard', icon: LayoutDashboard },
  { label: 'Modules', href: '/create/modules', icon: Brain },
  { label: 'My Twin', href: '/create/twin/chat', icon: MessageSquare },
];

const BRAND_NAV_ITEMS = [
  { label: 'Experiments', href: '/brand/experiments', icon: FlaskConical },
  { label: 'Chat', href: '/brand/chat', icon: MessageSquare },
  { label: 'New Experiment', href: '/brand/experiments/new', icon: Plus },
];

interface NavbarProps {
  side: 'create' | 'brand';
}

export function Navbar({ side }: NavbarProps) {
  const navItems = side === 'create' ? CREATE_NAV_ITEMS : BRAND_NAV_ITEMS;

  return (
    <header className="border-b border-darpan-border bg-darpan-bg/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="text-lg font-bold text-white shrink-0">
          <span className="text-darpan-lime">Darpan</span> Labs
        </Link>

        {/* Nav items */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </nav>

        {/* Side switcher */}
        <SideSwitcher side={side} />
      </div>
    </header>
  );
}
