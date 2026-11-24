
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg

from .models import (
    Product,
    Category,
    UserProfile,
    Order,
    OrderItem,
    Favorite,
    Review,
)


# РЕГИСТРАЦИЯ
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not all([username, email, phone, password, password2]):
            messages.error(request, 'Заполните все поля')
            return redirect('register')

        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')

        if len(password) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Это имя пользователя уже занято')
            return redirect('register')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Этот Email уже зарегистрирован')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        return redirect('home')

    return render(request, 'shop/register.html')


# ВХОД
def user_login(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        user = User.objects.filter(email__iexact=identifier).first()

        if user is None:
            user = User.objects.filter(username__iexact=identifier).first()

        if user:
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if authenticated_user:
                login(request, authenticated_user)
                return redirect('home')

        messages.error(request, 'Неверный Email, имя пользователя или пароль')

    return render(request, 'shop/login.html')


# ГЛАВНАЯ СТРАНИЦА
@login_required(login_url='login')
def home(request):
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    favorite_ids = Favorite.objects.filter(
        user=request.user
    ).values_list('product_id', flat=True)

    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories,
        'favorite_ids': favorite_ids,
    })


# ВЫХОД
def user_logout(request):
    logout(request)
    return redirect('login')


# ПРОФИЛЬ
@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()

        if request.FILES.get('photo'):
            user_profile.photo = request.FILES['photo']
            user_profile.save()

        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('profile')

    return render(request, 'shop/profile.html', {
        'profile': user_profile
    })


# ДОБАВИТЬ ИЛИ УДАЛИТЬ ИЗ ИЗБРАННОГО
@login_required(login_url='login')
def toggle_favorite(request, product_id):
    if request.method != 'POST':
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        favorite.delete()
        messages.success(request, 'Товар удалён из избранного')
    else:
        messages.success(request, 'Товар добавлен в избранное ❤️')

    return redirect(request.POST.get('next', 'home'))


# СТРАНИЦА ИЗБРАННОГО
@login_required(login_url='login')
def favorites(request):
    favorite_products = Favorite.objects.filter(
        user=request.user
    ).select_related('product', 'product__category')

    return render(request, 'shop/favorites.html', {
        'favorite_products': favorite_products,
    })


# ДОБАВИТЬ ТОВАР В КОРЗИНУ
@login_required(login_url='login')
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('home')

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    cart = request.session.get('cart', {})
    product_key = str(product.id)
    current_quantity = int(cart.get(product_key, 0))

    if product.stock <= current_quantity:
        messages.error(request, 'Недостаточно товара на складе')
    else:
        cart[product_key] = current_quantity + 1
        request.session['cart'] = cart
        messages.success(request, 'Товар добавлен в корзину')

    return redirect('home')


# КОРЗИНА
@login_required(login_url='login')
def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = Product.objects.filter(
            id=product_id,
            is_available=True
        ).first()

        if product:
            quantity = int(quantity)
            unit_price = product.discounted_price
            subtotal = unit_price * quantity

            items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
            })

            total += subtotal

    return render(request, 'shop/cart.html', {
        'items': items,
        'total': total,
    })


# ИЗМЕНИТЬ КОЛИЧЕСТВО
@login_required(login_url='login')
def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_key = str(product_id)

        product = get_object_or_404(Product, id=product_id)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity <= 0:
            cart.pop(product_key, None)

        elif quantity <= product.stock and product.is_available:
            cart[product_key] = quantity

        else:
            messages.error(request, 'Недостаточно товара на складе')

        request.session['cart'] = cart

    return redirect('cart')


# УДАЛИТЬ ТОВАР ИЗ КОРЗИНЫ
@login_required(login_url='login')
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart.pop(str(product_id), None)
        request.session['cart'] = cart

    return redirect('cart')


# ОФОРМЛЕНИЕ ЗАКАЗА
@login_required(login_url='login')
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.error(request, 'Корзина пуста')
        return redirect('cart')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not all([full_name, phone, address]):
            messages.error(request, 'Заполните обязательные поля')
            return redirect('checkout')

        try:
            with transaction.atomic():
                products = []

                for product_id, quantity in cart.items():
                    product = Product.objects.get(
                        id=product_id,
                        is_available=True
                    )

                    quantity = int(quantity)

                    if quantity <= 0 or quantity > product.stock:
                        raise ValueError(
                            f'Недостаточно товара: {product.name}'
                        )

                    products.append((product, quantity))

                total = sum(
                    (
                        product.discounted_price * quantity
                        for product, quantity in products
                    ),
                    Decimal('0.00')
                )

                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    address=address,
                    comment=comment,
                    total_price=total,
                )

                for product, quantity in products:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        price=product.discounted_price,
                        quantity=quantity,
                    )

                    product.stock -= quantity
                    product.save(update_fields=['stock'])

        except (Product.DoesNotExist, ValueError):
            messages.error(
                request,
                'Некоторые товары закончились. Проверьте корзину.'
            )
            return redirect('cart')

        request.session['cart'] = {}

        return redirect('order_success', order_id=order.id)

    items = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        product = Product.objects.filter(
            id=product_id,
            is_available=True
        ).first()

        if product:
            quantity = int(quantity)
            unit_price = product.discounted_price
            subtotal = unit_price * quantity

            items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'subtotal': subtotal,
            })

            total += subtotal

    if not items:
        messages.error(request, 'Товары в корзине больше недоступны')
        return redirect('cart')

    return render(request, 'shop/checkout.html', {
        'items': items,
        'total': total,
    })


# УСПЕШНЫЙ ЗАКАЗ
@login_required(login_url='login')
def order_success(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'shop/order_success.html', {
        'order': order
    })


# МОИ ЗАКАЗЫ
@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'shop/my_orders.html', {
        'orders': orders,
    })


# СТРАНИЦА ТОВАРА
def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    reviews = Review.objects.filter(
        product=product
    ).select_related('user')

    average_rating = reviews.aggregate(
        average=Avg('rating')
    )['average']

    user_review = None
    can_review = False

    if request.user.is_authenticated:
        user_review = reviews.filter(
            user=request.user
        ).first()

        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product
        ).exclude(
            order__status='cancelled'
        ).exists()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_count': reviews.count(),
        'user_review': user_review,
        'can_review': can_review,
    })


# ДОБАВИТЬ ИЛИ ИЗМЕНИТЬ ОТЗЫВ
@login_required(login_url='login')
def add_review(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    has_order = OrderItem.objects.filter(
        order__user=request.user,
        product=product
    ).exclude(
        order__status='cancelled'
    ).exists()

    if not has_order:
        messages.error(
            request,
            'Оставить отзыв могут только покупатели этого товара.'
        )
        return redirect('product_detail', product_id=product.id)

    try:
        rating = int(request.POST.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0

    text = request.POST.get('text', '').strip()

    if rating < 1 or rating > 5 or not text:
        messages.error(request, 'Выберите оценку и напишите отзыв.')
        return redirect('product_detail', product_id=product.id)

    Review.objects.update_or_create(
        user=request.user,
        product=product,
        defaults={
            'rating': rating,
            'text': text,
        }
    )

    messages.success(request, 'Ваш отзыв сохранён!')
    return redirect('product_detail', product_id=product.id)
