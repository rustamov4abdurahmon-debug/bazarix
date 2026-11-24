
from django.contrib import admin
from .models import (
    Category,
    Product,
    UserProfile,
    Order,
    OrderItem,
    Favorite,
    Review,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'price',
        'discount_percent',
        'discounted_price',
        'stock',
        'is_available',
    )
    list_filter = ('category', 'is_available', 'discount_percent')
    search_fields = ('name', 'description')
    list_editable = (
        'price',
        'discount_percent',
        'stock',
        'is_available',
    )
    readonly_fields = ('discounted_price',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product',
        'product_name',
        'price',
        'quantity',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'full_name',
        'phone',
        'address',
        'total_price',
        'status',
        'created_at',
    )

    list_filter = ('status', 'created_at')

    search_fields = (
        'full_name',
        'phone',
        'address',
        'comment',
    )

    list_editable = ('status',)

    readonly_fields = (
        'created_at',
        'total_price',
    )

    inlines = [OrderItemInline]

    fieldsets = (
        ('Информация о покупателе', {
            'fields': (
                'user',
                'full_name',
                'phone',
            )
        }),
        ('Доставка', {
            'fields': (
                'address',
                'comment',
            )
        }),
        ('Заказ', {
            'fields': (
                'total_price',
                'status',
                'created_at',
            )
        }),
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'product__name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'rating',
        'created_at',
    )

    list_filter = ('rating', 'created_at')

    search_fields = (
        'user__username',
        'product__name',
        'text',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )
