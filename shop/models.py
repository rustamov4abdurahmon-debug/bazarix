
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название категории'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название товара'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена'
    )
    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name='Скидка (%)'
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Фото'
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество на складе'
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name='Показывать на сайте'
    )

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            result = self.price * (
                Decimal('100') - Decimal(self.discount_percent)
            ) / Decimal('100')
            return result.quantize(Decimal('0.01'))

        return self.price

    @property
    def is_discounted(self):
        return self.discount_percent > 0

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        verbose_name='Фото профиля'
    )

    def __str__(self):
        return f'Профиль: {self.user.username}'

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'Готовится'),
        ('ready', 'Готов к выдаче'),
        ('delivering', 'Доставляется'),
        ('picked_up', 'Забран'),
        ('completed', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Покупатель'
    )

    full_name = models.CharField(
        max_length=200,
        verbose_name='Имя покупателя'
    )

    phone = models.CharField(
        max_length=30,
        verbose_name='Телефон'
    )

    address = models.TextField(
        verbose_name='Адрес доставки'
    )

    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Общая сумма'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='Статус заказа'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата заказа'
    )

    def __str__(self):
        return f'Заказ №{self.id} — {self.full_name}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Товар'
    )

    product_name = models.CharField(
        max_length=200,
        verbose_name='Название товара'
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за единицу'
    )

    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество'
    )

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Товар'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} — {self.product.name}'


class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Покупатель'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Товар'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        verbose_name='Оценка'
    )

    text = models.TextField(
        verbose_name='Текст отзыва'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата отзыва'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата изменения'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user.username} — {self.product.name} ({self.rating}/5)'
