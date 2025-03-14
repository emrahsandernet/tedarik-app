from django.contrib import admin
from .models import  Surec, Adim, SurecDurumu, GeriGonderme, Dosya



class AdimInline(admin.TabularInline):
    model = Adim
    extra = 1
    fields = ('ad', 'sira', 'kosul', 'onaylayanlar', 'departmanlar', 'sonraki_adim_kosulu')
    filter_horizontal = ('onaylayanlar', 'departmanlar')
    ordering = ('sira',)

@admin.register(Surec)
class SurecAdmin(admin.ModelAdmin):
    list_display = ( 'ad', 'aktif')
    list_filter = ( 'ad','aktif')
    search_fields = ('ad',)
    inlines = [AdimInline]

@admin.register(Adim)
class AdimAdmin(admin.ModelAdmin):
    list_display = ('surec', 'ad', 'sira')
    list_filter = ('surec',)
    search_fields = ('ad',)
    filter_horizontal = ('onaylayanlar', 'departmanlar')

class DosyaInline(admin.TabularInline):
    model = Dosya
    extra = 1
    readonly_fields = ('tarih', 'yukleyen')

@admin.register(SurecDurumu)
class SurecDurumuAdmin(admin.ModelAdmin):
    list_display = ('surec', 'mevcut_adim', 'is_completed', 'baslangic_tarihi')
    list_filter = ('is_completed', 'surec')
    search_fields = ('surec__ad', 'mevcut_adim__ad')
    filter_horizontal = ('tamamlanan_adimlar',)
    readonly_fields = ('baslangic_tarihi', 'tamamlanma_tarihi', 'son_islem_yapan')
    inlines = [DosyaInline]

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
    readonly_fields = ('tarih', 'yukleyen') 