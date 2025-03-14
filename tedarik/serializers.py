from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Departman, UserProfile, Urun, Tedarikci, Surec, Adim,
    MalzemeTalep, SurecDurumu, GeriGonderme, Dosya, Proje,
    SurecYorum, MalzemeTalepSatir, Malzeme,
)
class MalzemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Malzeme
        fields = ['id', 'ad', 'kategori', 'aciklama','birim']

class MalzemeTalepSatirSerializer(serializers.ModelSerializer):
    malzeme = MalzemeSerializer(read_only=True)
    malzeme_id = serializers.PrimaryKeyRelatedField(
        queryset=Malzeme.objects.all(),
        write_only=True,
        source='malzeme'
    )

    class Meta:
        model = MalzemeTalepSatir
        fields = ['id', 'talep', 'malzeme', 'malzeme_id', 'miktar']
        read_only_fields = ['talep']



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class DepartmanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departman
        fields = ['id', 'ad', 'aciklama']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    departman = DepartmanSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'departman']

class UrunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Urun
        fields = ['id', 'ad', 'aciklama', 'fiyat', 'stok']

class TedarikciSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tedarikci
        fields = ['id', 'ad', 'adres', 'telefon', 'email']
class DosyaSerializer(serializers.ModelSerializer):
    yukleyen = UserSerializer(read_only=True)

    class Meta:
        model = Dosya
        fields = ['id', 'surec_durumu', 'dosya', 'yukleyen', 'tarih']
        read_only_fields = ['tarih'] 


class SurecYorumSerializer(serializers.ModelSerializer):
    yazan = UserSerializer(read_only=True)
    dosyalar = DosyaSerializer(many=True, read_only=True)
    adim_detay = serializers.SerializerMethodField()

    class Meta:
        model = SurecYorum
        fields = ['id', 'surec_durumu', 'adim', 'adim_detay', 'yazan', 'yorum', 
                 'dosyalar', 'olusturma_tarihi', 'guncelleme_tarihi']
        read_only_fields = ['adim']

    def get_adim_detay(self, obj):
        return {
            'id': obj.adim.id,
            'ad': obj.adim.ad,
            'sira': obj.adim.sira
        } if obj.adim else None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        surec_durumu_id = self.context.get('surec_durumu_id')
        
        if surec_durumu_id:
            # Eğer bu yorum belirtilen süreç durumuna ait değilse, None döndür
            if str(instance.surec_durumu.id) != str(surec_durumu_id):
                return None
        
        return representation

class AdimSerializer(serializers.ModelSerializer):
    onaylayanlar = UserSerializer(many=True, read_only=True)
    departmanlar = DepartmanSerializer(many=True, read_only=True)
    yorumlar = serializers.SerializerMethodField()
    
    class Meta:
        model = Adim
        fields = ['id', 'surec', 'ad', 'sira', 'kosul', 'onaylayanlar', 
                 'departmanlar', 'sonraki_adim_kosulu', 'yorumlar']
    
    def get_yorumlar(self, obj):
        # Süreç durumu ID'sini context'ten al
        surec_durumu_id = self.context.get('surec_durumu_id')
        
        if surec_durumu_id:
            # Sadece bu süreç durumuna ve adıma ait yorumları getir
            yorumlar = obj.yorumlar.filter(surec_durumu_id=surec_durumu_id)
            return SurecYorumSerializer(yorumlar, many=True).data
        return []
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Süreç ID'sini context'ten al
        surec_id = self.context.get('surec_id')
        
        if surec_id:
            # Eğer bu adım belirtilen sürece ait değilse, None döndür
            if str(instance.surec.id) != str(surec_id):
                return None
        
        return representation

class SurecSerializer(serializers.ModelSerializer):
    adimlar = AdimSerializer(many=True, read_only=True)

    class Meta:
        model = Surec
        fields = ['id', 'ad', 'aciklama', 'aktif', 'kosullar', 'adimlar']
        
class ProjeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proje
        fields = ['id', 'ad', 'aciklama']


class BasitMalzemeTalepSerializer(serializers.ModelSerializer):
    olusturan = UserSerializer(read_only=True)
    proje = ProjeSerializer(read_only=True)
    malzemeler = MalzemeTalepSatirSerializer(source='satirlar', many=True, read_only=True)
    
    proje_id = serializers.PrimaryKeyRelatedField( 
        queryset=Proje.objects.all(),
        source='proje',
        write_only=True
    )

    son_islem_yapan = UserSerializer(read_only=True)
    olusturma_tarihi = serializers.DateTimeField(read_only=True)
    guncelleme_tarihi = serializers.DateTimeField(read_only=True)
  
    class Meta:
        model = MalzemeTalep
        fields = [
            'id', 'olusturan', 'proje', 'proje_id', 'durum', 'aciklama',
            'malzemeler', 'son_islem_yapan',
            'olusturma_tarihi', 'guncelleme_tarihi'
        ]

class SurecDurumuSerializer(serializers.ModelSerializer):
    siparis = BasitMalzemeTalepSerializer(read_only=True)
    surec = SurecSerializer(read_only=True)
    mevcut_adim = serializers.SerializerMethodField()
    tamamlanan_adimlar = serializers.SerializerMethodField()
    son_islem_yapan = UserSerializer(read_only=True)
    
    class Meta:
        model = SurecDurumu
        fields = [
            'id', 'siparis', 'surec', 'mevcut_adim', 'tamamlanan_adimlar',
            'is_completed', 'notlar', 'red_nedeni', 'son_islem_yapan',
            'baslangic_tarihi', 'tamamlanma_tarihi'
        ]
    
    def get_mevcut_adim(self, obj):
        return AdimSerializer(
            obj.mevcut_adim, 
            context={'surec_durumu_id': obj.id}
        ).data if obj.mevcut_adim else None
    
    def get_tamamlanan_adimlar(self, obj):
        return AdimSerializer(
            obj.tamamlanan_adimlar.all(), 
            many=True,
            context={'surec_durumu_id': obj.id}
        ).data

class MalzemeTalepSerializer(BasitMalzemeTalepSerializer):
    surec_durumu = serializers.SerializerMethodField()

    def get_surec_durumu(self, obj):
        try:
            surec_durumu = obj.tedarik_surec_durumu
            data = SurecDurumuSerializer(surec_durumu).data
            
            # Mevcut adıma ait yorumları filtrele
            
            return data
        except SurecDurumu.DoesNotExist:
            return None
            
    def create(self, validated_data):
        # Kullanıcıyı request'ten al
        user = self.context['request'].user
        validated_data['olusturan'] = user
        return super().create(validated_data)

    class Meta(BasitMalzemeTalepSerializer.Meta):
        fields = BasitMalzemeTalepSerializer.Meta.fields + ['surec_durumu']

class GeriGondermeSerializer(serializers.ModelSerializer):
    geri_gonderen = UserSerializer(read_only=True)

    class Meta:
        model = GeriGonderme
        fields = ['id', 'surec_durumu', 'red_nedeni', 'geri_gonderen', 'tarih']
        read_only_fields = ['tarih']

