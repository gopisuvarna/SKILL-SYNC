'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = document.cookie.includes('access_token');
    if (token) router.replace('/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4 text-cyan-400">AI SKILL SYNC Platform</h1>
      <p className="text-slate-400 mb-8">Skill gaps, career paths, job readiness</p>
      <div className="flex gap-4">
        <Link
          href="/login"
          className="px-6 py-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
        >
          Login
        </Link>
        <Link
          href="/register"
          className="px-6 py-3 rounded-lg border border-slate-600 hover:border-cyan-500 text-slate-200"
        >
          Register
        </Link>
      </div>
    </div>
  );
}
