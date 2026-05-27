from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, DoctorProfile


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    verbose_name_plural = "Doctor profile"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (DoctorProfileInline,)
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser")
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("MediSlot", {"fields": ("role",)}),)


admin.site.register(DoctorProfile)