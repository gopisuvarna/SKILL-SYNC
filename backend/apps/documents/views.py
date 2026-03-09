from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import fitz  # PyMuPDF
import uuid
import numpy as np

from .supabase_utils import upload_pdf_to_supabase
from rest_framework.permissions import AllowAny
from .supabase_utils import SupabaseConnectionError, SupabaseUploadError
from apps.skills.services.resume_skill_tool import SkillTool
from core.services.embedding_service import encode
from apps.roles.services.role_faiss_manager import get_role_faiss_manager



class ResumeUploadView(APIView):
    """
    Upload PDF → Extract Text → Extract Skills (NLP + LLM)
    """
    # Allow any caller; if a valid token/cookie is present, request.user will be set.
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            file = request.FILES.get("file")

            if not file:
                return Response(
                    {"error": "No file uploaded"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Only allow PDF
            if not (file.name or "").lower().endswith(".pdf"):
                return Response(
                    {"error": "Only PDF files are allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate unique filename
            filename = f"{uuid.uuid4()}_{file.name}"

            # Read bytes once (used for upload + text extraction)
            pdf_bytes = file.read()

            # 1️⃣ Upload to Supabase
            file_url = upload_pdf_to_supabase(pdf_bytes, filename)

            # 2️⃣ Extract text using PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()

            print("📄 Extracted Text Length:", len(extracted_text))

            if not extracted_text.strip():
                return Response(
                    {"error": "No text extracted from PDF"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3️⃣ Extract skills (skills app service)
            skills_data = SkillTool.run(extracted_text)

            # 4️⃣ Embed the skills (core embedding service, normalized for FAISS)
            if skills_data["all_skills"]:
                skills_vectors = encode(
                    skills_data["all_skills"],
                    normalize=True,
                    return_numpy=True,
                )
                query_vector = np.mean(skills_vectors, axis=0, keepdims=True)
                roles = get_role_faiss_manager().search(query_vector, top_k=30)
                print("✅ Roles searched successfully")
            else:
                roles = []

            

            # 4️⃣ Build recommended_roles for frontend (Roles tab)
            recommended_roles = [
                {
                    "role": meta.get("role", ""),
                    "description": meta.get("description", ""),
                    "skills": meta.get("skills", ""),
                    "score": round(score, 4),
                }
                for score, meta in roles
            ]

            # 5️⃣ Return response for frontend
            return Response({
                "message": "Skills extracted successfully",
                "file_url": file_url,
                "rule_based_skills": skills_data["rule_based_skills"],
                "llm_skills": skills_data["llm_skills"],
                "all_skills": skills_data["all_skills"],
                "recommended_roles": recommended_roles,
            }, status=status.HTTP_200_OK)

        except SupabaseConnectionError as e:
            print("❌ Supabase connection error:", str(e))
            return Response(
                {
                    "error": "Supabase is not reachable from the backend (connection timeout).",
                    "detail": str(e),
                    "hint": "Try a different network (mobile hotspot/VPN), allow outbound 443 in firewall, or change DNS (1.1.1.1 / 8.8.8.8).",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except SupabaseUploadError as e:
            print("❌ Supabase upload error:", str(e))
            return Response(
                {"error": "Supabase upload failed.", "detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            print("❌ Upload API Error:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
