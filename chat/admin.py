# chat/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import Channel, ChannelMembership, Message, Invitation
from users.models import User
    
@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'uuid', 'owner__username', 'owner__email')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'owner':
            kwargs['queryset'] = User.objects.order_by('username')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ChannelMembershipInline(admin.TabularInline):
    model = ChannelMembership
    extra = 1
    fields = ('user', 'is_admin', 'is_baned')
    autocomplete_fields = ('user',)

@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'is_admin', 'is_baned')
    list_filter = ('is_admin', 'is_baned', 'channel__name')
    search_fields = ('user__username', 'user__email', 'channel__name', 'channel__uuid')
    autocomplete_fields = ('user', 'channel')
    list_editable = ('is_admin', 'is_baned')
    ordering = ('user__username',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'channel')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user', 'content_preview', 'timestamp', 'uuid', 'created_at')
    list_filter = ('timestamp', 'created_at', 'channel__name')
    search_fields = ('content', 'user__username', 'user__email', 'channel__name', 'uuid')
    readonly_fields = ('uuid', 'timestamp', 'created_at', 'updated_at')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def content_preview(self, obj):
        """Показывает первые 50 символов сообщения"""
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Контент'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'channel')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.order_by('username')
        elif db_field.name == 'channel':
            kwargs['queryset'] = Channel.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('token', 'channel', 'author', 'expiration_period', 'expires_in', 'is_expired', 'created_at')
    list_filter = ('expiration_period', 'expires_in', 'created_at', 'channel__name')
    search_fields = ('token', 'channel__name', 'author__username', 'author__email')
    readonly_fields = ('token', 'expires_in', 'created_at', 'updated_at')
    date_hierarchy = 'expires_in'
    ordering = ('-created_at',)
    actions = ['renew_invitations']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('channel', 'author')

    def is_expired(self, obj):
        """Отображает статус истечения срока действия"""
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Истек?'

    def renew_invitations(self, request, queryset):
        """Продлевает срок действия выбранных приглашений на 24 часа"""
        updated = queryset.filter(expires_in__gt=timezone.now()).update(
            expires_in=timezone.now() + timezone.timedelta(hours=24),
            expiration_period='24'
        )
        self.message_user(request, f"Продлено {updated} приглашений.")
    renew_invitations.short_description = "Продлить приглашения на 24 часа"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            kwargs['queryset'] = User.objects.order_by('username')
        elif db_field.name == 'channel':
            kwargs['queryset'] = Channel.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)