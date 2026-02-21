"""Role listing view."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch

from .models import Role, RoleSkill
from .serializers import RoleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_roles(request):
    roles = Role.objects.prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    ).all()
    return Response(RoleSerializer(roles, many=True).data)

