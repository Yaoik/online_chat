from django.contrib import admin
from django.utils import timezone

from text_channels.models import Channel
from users.models import User

from .models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'channel', 'author', 'expiration_period', 'expires_in', 'is_expired', 'created_at')
    list_filter = ('expiration_period', 'expires_in', 'created_at', 'channel__name')
    search_fields = ('uuid', 'channel__name', 'author__username', 'author__email')
    readonly_fields = ('uuid', 'expires_in', 'created_at', 'updated_at')
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
