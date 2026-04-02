from django.contrib import admin

from .models import AppDatabase, CustomField, DatabaseMembership, Record


class CustomFieldInline(admin.TabularInline):
    model = CustomField
    fk_name = "database"
    extra = 0


class MembershipInline(admin.TabularInline):
    model = DatabaseMembership
    extra = 0


@admin.register(AppDatabase)
class AppDatabaseAdmin(admin.ModelAdmin):
    list_display = ("name", "use_case", "created_by", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CustomFieldInline, MembershipInline]


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("title", "database", "priority", "updated_at")
    list_filter = ("database", "priority")
    search_fields = ("title",)

# Register your models here.
