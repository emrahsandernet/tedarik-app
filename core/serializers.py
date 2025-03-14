from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Departman, Urun, Tedarikci

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class DepartmanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departman
        fields = '__all__'

class UrunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Urun
        fields = '__all__'

class TedarikciSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tedarikci
        fields = '__all__' 