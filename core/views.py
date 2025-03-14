from rest_framework import viewsets, permissions
from .models import Urun, Tedarikci, Departman
from .serializers import UrunSerializer, TedarikciSerializer, DepartmanSerializer
from workflow.serializers import UserSerializer
from django.contrib.auth.models import User

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.all()
    serializer_class = UrunSerializer
    permission_classes = [permissions.IsAuthenticated]

class TedarikciViewSet(viewsets.ModelViewSet):
    queryset = Tedarikci.objects.all()
    serializer_class = TedarikciSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepartmanViewSet(viewsets.ModelViewSet):
    queryset = Departman.objects.all()
    serializer_class = DepartmanSerializer
    permission_classes = [permissions.IsAuthenticated] 