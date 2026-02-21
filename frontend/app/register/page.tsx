'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'student' | 'teacher'>('student');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/register/', { email, password, role });
      router.push('/login');
      router.refresh();
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const msg = typeof res?.detail === 'string' ? res.detail : res?.email?.[0] || res?.password?.[0] || 'Registration failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-6">
        <h1 className="text-2xl font-bold text-cyan-400">Register</h1>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
        />
        <input
          type="password"
          placeholder="Password (min 8 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as 'student' | 'teacher')}
          className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-600 text-white focus:border-cyan-500 focus:outline-none"
        >
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
        </select>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium"
        >
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
        <p className="text-slate-400 text-sm">
          Have an account? <Link href="/login" className="text-cyan-400 hover:underline">Login</Link>
        </p>
      </form>
    </div>
  );
}
