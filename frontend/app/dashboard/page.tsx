'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

interface DashboardData {
  skill_distribution: { skill: string }[];
  match_score: number;
  top_roles: { id: string; title: string; match_score: number }[];
  skill_gaps: { missing_skills: string[]; coverage_percent: number };
  learning_plan: { id: string; title: string; provider: string; url: string; matched_skills: string[] }[];
  job_matches: { id: string; title: string; company: string; url: string; matched_skills: string[] }[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<DashboardData>('/analytics/dashboard/')
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-400">Loading dashboard...</div>;
  if (!data) return <div className="text-slate-400">Unable to load dashboard.</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">Career Overview</h1>

      <section>
        <h2 className="text-lg font-semibold mb-3">Your Skills</h2>
        <div className="flex flex-wrap gap-2">
          {data.skill_distribution.length ? (
            data.skill_distribution.map((s) => (
              <span key={s.skill} className="px-3 py-1 rounded-full bg-slate-800 text-cyan-300 text-sm">
                {s.skill}
              </span>
            ))
          ) : (
            <Link href="/dashboard/skills" className="text-cyan-400 hover:underline">
              Add skills
            </Link>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Match Score</h2>
        <p className="text-3xl text-cyan-400">{(data.match_score * 100).toFixed(0)}%</p>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Top Recommended Roles</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.top_roles.map((r) => (
            <Link
              key={r.id}
              href={`/dashboard/roles?id=${r.id}`}
              className="block p-4 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50"
            >
              <h3 className="font-medium">{r.title}</h3>
              <p className="text-slate-400 text-sm mt-1">{(r.match_score * 100).toFixed(0)}% match</p>
            </Link>
          ))}
        </div>
      </section>

      {data.skill_gaps?.missing_skills?.length ? (
        <section>
          <h2 className="text-lg font-semibold mb-3">Skill Gaps (Coverage: {data.skill_gaps.coverage_percent}%)</h2>
          <div className="flex flex-wrap gap-2">
            {data.skill_gaps.missing_skills.map((s) => (
              <span key={s} className="px-3 py-1 rounded-full bg-amber-900/50 text-amber-300 text-sm">
                {s}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      {data.learning_plan?.length ? (
        <section>
          <h2 className="text-lg font-semibold mb-3">Learning Recommendations</h2>
          <div className="space-y-2">
            {data.learning_plan.slice(0, 5).map((c) => (
              <a
                key={c.id}
                href={c.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50"
              >
                <h3 className="font-medium">{c.title}</h3>
                <p className="text-slate-400 text-sm">{c.provider} · {c.matched_skills.join(', ')}</p>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      {data.job_matches?.length ? (
        <section>
          <h2 className="text-lg font-semibold mb-3">Job Matches</h2>
          <div className="space-y-2">
            {data.job_matches.map((j) => (
              <a
                key={j.id}
                href={j.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 rounded-lg bg-slate-800/50 border border-slate-700 hover:border-cyan-500/50"
              >
                <h3 className="font-medium">{j.title}</h3>
                <p className="text-slate-400 text-sm">{j.company} · {j.matched_skills.join(', ')}</p>
              </a>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
