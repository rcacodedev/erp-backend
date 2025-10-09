from django.contrib import admin
from core.models import Organization, Membership

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name","slug","trial_ends_at","created_at")
    search_fields = ("name","slug")

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("organization","user","role","created_at")
    search_fields = ("organization__name","organization__slug","user__email")
