'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';

interface Role {
  id: string;
  title: string;
  description: string;
  match_score?: number;
}

export default function RolesPage() {
  const searchParams = useSearchParams();
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ roles: Role[] }>('/recommendations/roles/')
      .then((r) => setRoles(r.data.roles || []))
      .catch(() => [])
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-400">Loading roles...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Recommended Roles</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {roles.map((r) => (
          <div key={r.id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <h3 className="font-medium">{r.title}</h3>
            {r.match_score != null && (
              <p className="text-cyan-400 text-sm mt-1">{(r.match_score * 100).toFixed(0)}% match</p>
            )}
            {r.description && <p className="text-slate-400 text-sm mt-2 line-clamp-2">{r.description}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
