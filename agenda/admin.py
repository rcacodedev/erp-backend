from django.contrib import admin
from .models import Event, Note

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id","org","title","start","end","all_day","is_important","status")
    list_filter = ("org","is_important","status","all_day")
    search_fields = ("title","notes")

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id","org","title","is_task","status","due_date","is_important","is_pinned")
    list_filter = ("org","is_task","status","is_important","is_pinned")
    search_fields = ("title","body")
