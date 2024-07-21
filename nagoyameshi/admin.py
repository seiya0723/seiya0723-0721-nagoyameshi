from django.contrib import admin
from .models import ExtendedModel, Category, Day, Restaurant, RestaurantPhoto, Review
from django.utils.safestring import mark_safe

admin.site.register(ExtendedModel)

class DayAdmin(admin.ModelAdmin):
    list_display = ('name', 'key')

admin.site.register(Day, DayAdmin)

# カテゴリー
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'deleted_at', 'updated_at', 'created_at')

admin.site.register(Category, CategoryAdmin)

# 店舗
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_id', 'description', 'floor_price', 'maximum_price', 'opening_time',
                    'closing_time', 'postal_code', 'city', 'street_address', 'phone_number', 'get_regular_closing_day')
    search_fields = ('name', )
    list_filter = ('category_id', )

    # def get_regular_closing_day(self, obj):
    #     return "\n".join([day.name for day in obj.regular_closing_day.all()])
    
    # def image(self, obj):
    #     return mark_safe('<img scr="{}" style="width:100px height:auto;">'.format(obj.thumbnail.url))

admin.site.register(Restaurant, RestaurantAdmin)

# 店舗画像（詳細）
class RestaurantPhotoAdmin(admin.ModelAdmin):
    list_display = ('image_view', 'restaurant_id')

    def image_view(self, obj):
        return mark_safe('<img src="{}" style="width:100px height:auto;">'.format(obj.image.url))

admin.site.register(RestaurantPhoto, RestaurantPhotoAdmin)

# レビュー
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant_id', 'user_id', 'comment', 'deleted_at', 'updated_at', 'created_at')
    list_filter = ('restaurant_id', 'user_id')

admin.site.register(Review, ReviewAdmin)