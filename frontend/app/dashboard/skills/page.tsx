'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface UserSkill {
  id: string;
  skill_name: string;
  source: string;
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<UserSkill[]>([]);
  const [newSkill, setNewSkill] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSkills();
  }, []);

  function loadSkills() {
    api
      .get<UserSkill[]>('/skills/')
      .then((r) => setSkills(r.data))
      .catch(() => [])
      .finally(() => setLoading(false));
  }

  async function addSkill(e: React.FormEvent) {
    e.preventDefault();
    if (!newSkill.trim()) return;
    try {
      await api.post('/skills/', { name: newSkill.trim() });
      setNewSkill('');
      loadSkills();
    } catch {
      // ignore
    }
  }

  async function removeSkill(id: string) {
    try {
      await api.delete(`/skills/${id}/`);
      loadSkills();
    } catch {
      // ignore
    }
  }

  if (loading) return <div className="text-slate-400">Loading skills...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Skills</h1>
      <form onSubmit={addSkill} className="mb-6 flex gap-2">
        <input
          type="text"
          placeholder="Add skill"
          value={newSkill}
          onChange={(e) => setNewSkill(e.target.value)}
          className="flex-1 px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
        />
        <button type="submit" className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium">
          Add
        </button>
      </form>
      <div className="flex flex-wrap gap-2">
        {skills.map((s) => (
          <span
            key={s.id}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 text-cyan-300 text-sm"
          >
            {s.skill_name}
            <button onClick={() => removeSkill(s.id)} className="text-slate-400 hover:text-red-400 text-xs">
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
