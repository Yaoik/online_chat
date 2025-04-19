from django.contrib import admin

from users.models import User

from .models import Channel, ChannelMembership


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
