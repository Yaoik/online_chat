# chat/admin.py
from django.contrib import admin

from text_channels.models import Channel
from users.models import User

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('channel', 'user', 'content_preview', 'uuid', 'created_at')
    list_filter = ('created_at', 'channel__name')
    search_fields = ('content', 'user__username', 'user__email', 'channel__name', 'uuid')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

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
