from django.contrib import admin
from .models import (
    Urun, Tedarikci, MalzemeTalep, Surec, Adim, 
    SurecDurumu, Departman, UserProfile, GeriGonderme, Dosya, Proje,
    MalzemeTalepSatir, Malzeme, MalzemeKategori
)
from django.contrib.admin import register

@admin.register(MalzemeKategori)
class MalzemeKategoriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)

@admin.register(Malzeme)
class MalzemeAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kategori', 'stok')
    search_fields = ('ad',)
    list_filter = ('kategori',)

@admin.register(MalzemeTalepSatir)
class MalzemeTalepSatirAdmin(admin.ModelAdmin):
    list_display = ('talep', 'malzeme', 'miktar')
    search_fields = ('talep__proje__ad', 'malzeme__ad')
    list_filter = ('talep__proje', 'malzeme')


@admin.register(Proje)
class ProjeAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)

@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ('ad', 'fiyat', 'stok')
    search_fields = ('ad',)

@admin.register(Tedarikci)
class TedarikciAdmin(admin.ModelAdmin):
    list_display = ('ad', 'telefon', 'email')
    search_fields = ('ad', 'email')

class AdimInline(admin.StackedInline):
    model = Adim
    extra = 1  # Kaç tane boş form gösterileceği
    filter_horizontal = ('onaylayanlar', 'departmanlar')  # Çoklu seçim için daha iyi bir arayüz
    ordering = ('sira',)

    fieldsets = (
        (None, {
            'fields': ('ad', 'sira', 'kosul', 'sonraki_adim_kosulu')  # Burada ad, sira ve kosul alanlarını bir arada gösteriyoruz
        }),
        ('Onaylayıcılar', {
            'classes': ('collapse',),
            'fields': ('onaylayanlar', 'departmanlar')
        }),
    )

@admin.register(Surec)
class SurecAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aktif')
    search_fields = ('ad',)
    inlines = [AdimInline]
    fieldsets = (
        (None, {
            'fields': ('ad', 'aciklama', 'aktif')
        }),
        ('Gelişmiş Seçenekler', {
            'classes': ('collapse',),
            'fields': ('kosullar',),
        }),
    )

@admin.register(Adim)
class AdimAdmin(admin.ModelAdmin):
    list_display = ('surec', 'ad', 'sira')
    list_filter = ('surec',)
    search_fields = ('ad',)
    filter_horizontal = ('onaylayanlar', 'departmanlar')
    fieldsets = (
        (None, {
            'fields': ('surec', 'ad', 'sira')
        }),
        ('Onaylayıcılar', {
            'fields': ('onaylayanlar', 'departmanlar')
        }),
        ('Koşullar', {
            'classes': ('collapse',),
            'fields': ('kosul', 'sonraki_adim_kosulu'),
        }),
    )

@admin.register(MalzemeTalep)  
class MalzemeTalepAdmin(admin.ModelAdmin):
    list_display = ('olusturan', 'proje', 'durum', 'olusturma_tarihi')
    list_filter = ('durum', 'proje')
    search_fields = ('olusturan__username', 'proje__ad')
    date_hierarchy = 'olusturma_tarihi'
    readonly_fields = ('olusturma_tarihi', 'guncelleme_tarihi', 'son_islem_yapan')
    fieldsets = (
        (None, {
            'fields': ('olusturan', 'proje', 'aciklama')
        }),
        ('Süreç Bilgileri', {
            'fields': ('durum', 'son_islem_yapan')
        }),
        ('Sistem Bilgileri', {
            'classes': ('collapse',),
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
        }),
    )

class DosyaInline(admin.TabularInline):
    model = Dosya
    extra = 1
    readonly_fields = ('tarih',)

@admin.register(SurecDurumu)
class SurecDurumuAdmin(admin.ModelAdmin):
    list_display = ('siparis', 'surec', 'mevcut_adim', 'is_completed', 'baslangic_tarihi')
    list_filter = ('is_completed', 'surec')
    search_fields = ('siparis__proje__ad',)
    date_hierarchy = 'baslangic_tarihi'
    readonly_fields = ('baslangic_tarihi', 'tamamlanma_tarihi', 'son_islem_yapan')
    filter_horizontal = ('tamamlanan_adimlar',)
    inlines = [DosyaInline]
    fieldsets = (
        (None, {
            'fields': ('siparis', 'surec', 'mevcut_adim')
        }),
        ('Durum Bilgileri', {
            'fields': ('is_completed', 'notlar', 'red_nedeni')
        }),
        ('Tamamlanan Adımlar', {
            'fields': ('tamamlanan_adimlar',)
        }),
        ('Sistem Bilgileri', {
            'classes': ('collapse',),
            'fields': ('son_islem_yapan', 'baslangic_tarihi', 'tamamlanma_tarihi'),
        }),
    )

@admin.register(Departman)
class DepartmanAdmin(admin.ModelAdmin):
    search_fields = ['ad']
    list_display = ['ad', 'aciklama']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'departman']
    list_filter = ['departman']
    search_fields = ['user__username', 'departman__ad']
    raw_id_fields = ['user']  # autocomplete_fields yerine raw_id_fields kullanalım

@admin.register(GeriGonderme)
class GeriGondermeAdmin(admin.ModelAdmin):
    list_display = ('surec_durumu', 'geri_gonderen', 'tarih')
    list_filter = ('geri_gonderen',)
    search_fields = ('red_nedeni',)
    date_hierarchy = 'tarih'
    readonly_fields = ('tarih',)

@admin.register(Dosya)
class DosyaAdmin(admin.ModelAdmin):
    list_display = ('surec_durumu', 'yukleyen', 'tarih')
    list_filter = ('yukleyen',)
    search_fields = ('dosya',)
    date_hierarchy = 'tarih'
    readonly_fields = ('tarih',)
