'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Document {
  id: string;
  file_url: string;
  uploaded_at: string;
  parsed: boolean;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Document[]>('/documents/').then((r) => setDocs(r.data)).catch(() => []).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-400">Loading documents...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Documents</h1>
      <p className="text-slate-400 mb-4">
        Use the API: POST /api/documents/presigned/ to get a pre-signed URL, then upload directly to S3, then POST
        /api/documents/confirm/ with object_key.
      </p>
      <div className="space-y-3">
        {docs.map((d) => (
          <div key={d.id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <a href={d.file_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
              {d.file_url.split('/').pop()}
            </a>
            <p className="text-slate-400 text-sm mt-1">Parsed: {d.parsed ? 'Yes' : 'No'}</p>
            <p className="text-slate-500 text-xs">{new Date(d.uploaded_at).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
