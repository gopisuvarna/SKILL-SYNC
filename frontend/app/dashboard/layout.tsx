'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { User } from '@/lib/auth';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<User>('/auth/me/')
      .then((r) => setUser(r.data))
      .catch(() => router.push('/login'))
      .finally(() => setLoading(false));
  }, [router]);

  async function logout() {
    await api.post('/auth/logout/');
    router.push('/login');
    router.refresh();
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  const nav = [
    { href: '/dashboard', label: 'Overview' },
    { href: '/dashboard/documents', label: 'Documents' },
    { href: '/dashboard/skills', label: 'Skills' },
    { href: '/dashboard/roles', label: 'Roles' },
    { href: '/dashboard/jobs', label: 'Jobs' },
    { href: '/dashboard/chat', label: 'Career Mentor' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <Link href="/dashboard" className="text-xl font-bold text-cyan-400">
          Career AI
        </Link>
        <nav className="flex gap-4">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={`text-sm ${pathname === n.href ? 'text-cyan-400' : 'text-slate-400 hover:text-white'}`}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-sm">{user?.email}</span>
          <button onClick={logout} className="text-slate-400 hover:text-white text-sm">
            Logout
          </button>
        </div>
      </header>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
