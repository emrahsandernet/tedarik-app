from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SatinAlmaSiparisi
from .serializers import SatinAlmaSiparisiSerializer, SatinAlmaSiparisiCreateSerializer
from workflow.engine import WorkflowEngine

class SatinAlmaSiparisiViewSet(viewsets.ModelViewSet):
    queryset = SatinAlmaSiparisi.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SatinAlmaSiparisiCreateSerializer
        return SatinAlmaSiparisiSerializer
    
    def get_queryset(self):
        # Kullanıcıya göre filtreleme
        user = self.request.user
        if user.is_staff:
            return SatinAlmaSiparisi.objects.all()
        return SatinAlmaSiparisi.objects.filter(olusturan=user)
    
    @action(detail=True, methods=['post'])
    def adim_onayla(self, request, pk=None):
        """Mevcut adımı onaylar ve bir sonraki adıma geçer"""
        siparis = self.get_object()
        
        if not siparis.surec_durumu:
            return Response(
                {"error": "Bu sipariş için aktif bir süreç durumu bulunamadı."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            engine = WorkflowEngine(siparis.surec_durumu, request.user)
            engine.process_step(request.data)
            return Response({"message": "Adım onaylandı"})
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def adim_reddet(self, request, pk=None):
        """Mevcut adımı reddeder"""
        siparis = self.get_object()
        
        try:
            engine = WorkflowEngine(siparis.surec_durumu, request.user)
            engine.reject_step(request.data)
            return Response({"message": "Adım reddedildi"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 