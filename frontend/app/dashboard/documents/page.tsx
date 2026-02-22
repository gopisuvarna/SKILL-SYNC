// 'use client';

// import { useEffect, useState } from 'react';
// import { api } from '@/lib/api';

// interface Document {
//   id: string;
//   file_url: string;
//   uploaded_at: string;
//   parsed: boolean;
// }

// export default function DocumentsPage() {
//   const [docs, setDocs] = useState<Document[]>([]);
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     api.get<Document[]>('/documents/').then((r) => setDocs(r.data)).catch(() => []).finally(() => setLoading(false));
//   }, []);

//   if (loading) return <div className="text-slate-400">Loading documents...</div>;

//   return (
//     <div>
//       <h1 className="text-2xl font-bold mb-6">Documents</h1>
//       <p className="text-slate-400 mb-4">
//         Use the API: POST /api/documents/presigned/ to get a pre-signed URL, then upload directly to S3, then POST
//         /api/documents/confirm/ with object_key.
//       </p>
//       <div className="space-y-3">
//         {docs.map((d) => (
//           <div key={d.id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
//             <a href={d.file_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">
//               {d.file_url.split('/').pop()}
//             </a>
//             <p className="text-slate-400 text-sm mt-1">Parsed: {d.parsed ? 'Yes' : 'No'}</p>
//             <p className="text-slate-500 text-xs">{new Date(d.uploaded_at).toLocaleString()}</p>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }

"use client";

import { useState } from "react";
import axios from "axios";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [ruleSkills, setRuleSkills] = useState<string[]>([]);
  const [llmSkills, setLlmSkills] = useState<string[]>([]);
  const [allSkills, setAllSkills] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // File change handler
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setMessage("");
      setRuleSkills([]);
      setLlmSkills([]);
      setAllSkills([]);
    }
  };

  // Upload + Extract Skills
  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("Uploading & Extracting Skills... 🤖");

      const response = await axios.post(
        "http://127.0.0.1:8000/api/documents/",
        formData,
        {
          withCredentials: true,
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log("API Response:", response.data);

      // 🔥 MATCHING BACKEND RESPONSE EXACTLY
      setRuleSkills(response.data.rule_based_skills || []);
      setLlmSkills(response.data.llm_skills || []);
      setAllSkills(response.data.all_skills || []);

      setMessage("Skills extracted successfully! 🚀");
    } catch (error: any) {
      console.error("Upload Error:", error);
      if (error.response) {
        console.error("Backend Error:", error.response.data);
        setMessage(
          error.response.data?.error ||
            "Backend error occurred!"
        );
      } else {
        setMessage("Cannot connect to backend server!");
      }
    } finally {
      setLoading(false);
    }
  };

  const SkillSection = ({
    title,
    skills,
    color,
  }: {
    title: string;
    skills: string[];
    color: string;
  }) => (
    <div className="bg-gray-900 p-6 rounded-xl shadow-lg">
      <h2 className={`text-2xl font-bold mb-4 ${color}`}>
        {title}
      </h2>

      {skills.length === 0 ? (
        <p className="text-gray-400">No skills detected</p>
      ) : (
        <div className="flex flex-wrap gap-3">
          {skills.map((skill, index) => (
            <span
              key={index}
              className="bg-blue-600 px-4 py-2 rounded-full text-sm font-medium shadow"
            >
              {skill}
            </span>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-black flex items-center justify-center text-white p-6">
      <div className="bg-gray-800 shadow-2xl rounded-2xl p-8 w-full max-w-5xl">
        <h1 className="text-3xl font-bold text-center mb-6">
          AI Resume Skill Extractor 🧠📄
        </h1>

        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full mb-4 text-sm text-gray-300
          file:mr-4 file:py-3 file:px-6
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-600 file:text-white
          hover:file:bg-blue-700 cursor-pointer"
        />

        {file && (
          <p className="mb-4 text-green-400">
            Selected File:{" "}
            <span className="font-semibold">{file.name}</span>
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 transition duration-300 py-3 rounded-xl font-semibold disabled:opacity-50"
        >
          {loading ? "Processing Resume..." : "Upload & Extract Skills"}
        </button>

        <p className="mt-4 text-center text-yellow-400">
          {message}
        </p>

        {(ruleSkills.length > 0 ||
          llmSkills.length > 0 ||
          allSkills.length > 0) && (
          <div className="mt-10 space-y-6">
            <SkillSection
              title="🔥 Final Combined Skills"
              skills={allSkills}
              color="text-yellow-400"
            />

            <SkillSection
              title="📚 NLP Skills (spaCy + skills.txt)"
              skills={ruleSkills}
              color="text-green-400"
            />

            <SkillSection
              title="🤖 LLM Skills (Gemini - Unseen Skills)"
              skills={llmSkills}
              color="text-purple-400"
            />
          </div>
        )}
      </div>
    </div>
  );
}
