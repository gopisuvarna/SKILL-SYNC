'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  matched_skills?: string[];
  all_skills?: string[];
}

export default function JobsPage() {
  const [matched, setMatched] = useState<Job[]>([]);
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<{ results: Job[] }>('/jobs/matched/').then((r) => r.data.results),
      api.get<{ results: Job[] }>('/jobs/').then((r) => r.data.results),
    ])
      .then(([m, a]) => {
        setMatched(m || []);
        setAllJobs(a || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-400">Loading jobs...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Jobs</h1>
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4">Matched to Your Skills</h2>
        <div className="space-y-3">
          {matched.map((j) => (
            <a
              key={j.id}
              href={j.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50"
            >
              <h3 className="font-medium">{j.title}</h3>
              <p className="text-slate-400 text-sm">{j.company} · {j.location}</p>
              {j.matched_skills?.length ? (
                <p className="text-cyan-400 text-sm mt-1">Matched: {j.matched_skills.join(', ')}</p>
              ) : null}
            </a>
          ))}
        </div>
      </section>
      <section>
        <h2 className="text-lg font-semibold mb-4">All Jobs</h2>
        <div className="space-y-3">
          {allJobs.map((j) => (
            <a
              key={j.id}
              href={j.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50"
            >
              <h3 className="font-medium">{j.title}</h3>
              <p className="text-slate-400 text-sm">{j.company} · {j.location}</p>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
