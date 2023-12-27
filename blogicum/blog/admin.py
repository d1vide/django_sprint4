from django.contrib import admin

from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'created_at',
        'pub_date',
        'is_published',
    )
    list_editable = (
        'is_published',
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'created_at',
        'slug'
    )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Location)
admin.site.register(Post, PostAdmin)
