from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, UserSession, GuestSession, LoginAttempt


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'role', 'verified', 'two_factor_enabled', 'created_at')
    list_filter = ('role', 'verified', 'two_factor_enabled', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'verified')
        }),
        ('Profile Details', {
            'fields': ('profile_picture', 'bio', 'phone_number')
        }),
        ('Security', {
            'fields': ('two_factor_enabled',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'device_name', 'ip_address', 'get_status', 'last_activity')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'ip_address', 'device_name')
    readonly_fields = ('session_key', 'created_at', 'last_activity', 'user_agent')
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_key', 'device_name')
        }),
        ('Connection Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Timeline', {
            'fields': ('created_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    get_status.short_description = 'Status'


@admin.register(GuestSession)
class GuestSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_status', 'ip_address', 'created_at', 'expires_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('id', 'ip_address')
    readonly_fields = ('id', 'token', 'created_at', 'user_agent')
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'token')
        }),
        ('Connection Details', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'expires_at')
        }),
        ('Session Data', {
            'fields': ('session_data',),
            'classes': ('collapse',)
        }),
    )
    
    def get_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Expired</span>')
    get_status.short_description = 'Status'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'get_success', 'timestamp')
    list_filter = ('success', 'timestamp')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('username', 'ip_address', 'user_agent', 'success', 'timestamp')
    
    def has_add_permission(self, request):
        return False  # Login attempts are recorded automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Login attempts are immutable
    
    def get_success(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    get_success.short_description = 'Status'
