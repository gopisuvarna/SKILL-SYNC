# """AI Career Mentor chatbot using Google AI Studio."""
# import logging
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.conf import settings
# from django.db.models import Prefetch

# from apps.skills.models import UserSkill
# from apps.roles.models import Role, RoleSkill
# from apps.roles.services import compute_skill_gap

# logger = logging.getLogger(__name__)

# SYSTEM_PROMPT = """You are an expert AI career mentor helping users understand skill gaps, career paths, and job readiness.
# Be concise, actionable, and supportive. Use the provided context about the user's skills, recommended roles, and missing skills."""


# def _build_context(user) -> str:
#     user_skills = list(UserSkill.objects.filter(user=user).select_related('skill').values_list('skill__name', flat=True))
#     user_skill_ids = {str(sid) for sid in UserSkill.objects.filter(user=user).values_list('skill_id', flat=True)}

#     roles = Role.objects.prefetch_related(Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))).order_by('?')[:3]
#     context_parts = [f"User skills: {', '.join(user_skills) or 'None'}"]

#     for role in roles:
#         rs_list = [{'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight} for rs in role.skills.all()]
#         gap = compute_skill_gap(user_skill_ids, rs_list)
#         context_parts.append(f"Role: {role.title}. Missing skills: {', '.join(gap['missing_skills']) or 'None'}. Coverage: {gap['coverage_percent']}%")

#     return "\n".join(context_parts)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def chat(request):
#     messages = request.data.get('messages', [])
#     if not messages:
#         return Response({'detail': 'messages required'}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         import google.generativeai as genai
#         genai.configure(api_key=settings.GOOGLE_AI_CONFIG.get('API_KEY'))
#         model = genai.GenerativeModel('gemini-pro')

#         context = _build_context(request.user)
#         system = f"{SYSTEM_PROMPT}\n\nContext:\n{context}"

#         history = [{'role': 'user' if m.get('role') == 'user' else 'model', 'parts': [m.get('content', '')]} for m in messages[:-1]]
#         last_msg = messages[-1].get('content', '') if messages else ''

#         chat_session = model.start_chat(history=history)
#         response = chat_session.send_message(f"{system}\n\nUser: {last_msg}")

#         return Response({'message': response.text})
#     except Exception as e:
#         logger.exception("Chatbot error: %s", e)
#         return Response({'detail': 'Chatbot unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

"""
AI Career Mentor chatbot using Groq.
"""

import logging
from django.conf import settings
from django.db.models import Prefetch

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from groq import Groq

from apps.skills.models import UserSkill
from apps.roles.models import Role, RoleSkill
from apps.roles.services import compute_skill_gap

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert AI career mentor helping users understand skill gaps, career paths, and job readiness.

Guidelines:
- Be concise and actionable.
- Be supportive and motivating.
- Use the provided context about the user's skills and role gaps.
- Suggest learning paths when skills are missing.
- Keep responses clear and structured.
"""


# -----------------------------------
# Build Dynamic User Context
# -----------------------------------
def _build_context(user) -> str:
    # Fetch user's skills
    user_skills = list(
        UserSkill.objects.filter(user=user)
        .select_related("skill")
        .values_list("skill__name", flat=True)
    )

    user_skill_ids = {
        str(sid)
        for sid in UserSkill.objects.filter(user=user).values_list(
            "skill_id", flat=True
        )
    }

    # Fetch 3 random roles
    roles = (
        Role.objects.prefetch_related(
            Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
        )
        .order_by("?")[:3]
    )

    context_parts = [
        f"User skills: {', '.join(user_skills) if user_skills else 'None'}"
    ]

    for role in roles:
        rs_list = [
            {
                "skill_id": str(rs.skill_id),
                "skill_name": rs.skill.name,
                "importance_weight": rs.importance_weight,
            }
            for rs in role.skills.all()
        ]

        gap = compute_skill_gap(user_skill_ids, rs_list)

        context_parts.append(
            f"Role: {role.title}\n"
            f"Missing skills: {', '.join(gap['missing_skills']) if gap['missing_skills'] else 'None'}\n"
            f"Coverage: {gap['coverage_percent']}%"
        )

    return "\n\n".join(context_parts)


# -----------------------------------
# Chat API
# -----------------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    messages = request.data.get("messages", [])

    if not messages:
        return Response(
            {"detail": "messages required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Initialize Groq client
        client = Groq(api_key=settings.GROQ_API_KEY)

        # Build user-specific context
        context = _build_context(request.user)

        system_message = f"{SYSTEM_PROMPT}\n\nContext:\n{context}"

        # Format conversation history
        formatted_messages = [
            {"role": "system", "content": system_message}
        ]

        for msg in messages:
            role = "user" if msg.get("role") == "user" else "assistant"
            formatted_messages.append(
                {
                    "role": role,
                    "content": msg.get("content", ""),
                }
            )

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Change if needed
            messages=formatted_messages,
            temperature=0.3,
            max_tokens=800,
        )

        reply = response.choices[0].message.content.strip()

        return Response({"message": reply})

    except Exception as e:
        logger.exception("Chatbot error: %s", e)
        return Response(
            {"detail": "Chatbot unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )