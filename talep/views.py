from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MalzemeTalebi, TalepKalemi
from .serializers import MalzemeTalebiSerializer, TalepKalemiSerializer
from workflow.engine import WorkflowEngine

class MalzemeTalebiViewSet(viewsets.ModelViewSet):
    queryset = MalzemeTalebi.objects.all()
    serializer_class = MalzemeTalebiSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def adim_onayla(self, request, pk=None):
        """Mevcut adımı onaylar ve bir sonraki adıma geçer"""
        talep = self.get_object()
        
        try:
            engine = WorkflowEngine(talep.surec_durumu, request.user)
            engine.process_step({})
            return Response(
                {"message": "Adım onaylandı"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class TalepKalemiViewSet(viewsets.ModelViewSet):
    queryset = TalepKalemi.objects.all()
    serializer_class = TalepKalemiSerializer
    permission_classes = [permissions.IsAuthenticated] 