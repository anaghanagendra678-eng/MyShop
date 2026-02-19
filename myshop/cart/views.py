from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CartItem
from products.models import Product, Order, OrderItem
from django.contrib import messages

# Add product to cart
@login_required(login_url='login')
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart')

# Display cart
@login_required(login_url='login')
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal for item in cart_items)
    return render(request, 'cart/cart.html', {'items': cart_items, 'total': total})

# Remove item from cart
@login_required(login_url='login')
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    item.delete()
    return redirect('cart')

# Increment item quantity
@login_required(login_url='login')
def increment_item(request, pk):
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    item.quantity += 1
    item.save()
    return redirect('cart')

# Decrement item quantity
@login_required(login_url='login')
def decrement_item(request, pk):
    item = get_object_or_404(CartItem, pk=pk, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('cart')

@login_required(login_url='login')
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal for item in cart_items)

    if request.method == "POST":
        address = request.POST.get("address")
        payment_method = request.POST.get("payment_method")

        # Create order
        order = Order.objects.create(
            user=request.user,
            total=total,
            address=address,
            payment_method=payment_method
        )

        # Add items to order
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        # Clear cart
        cart_items.delete()

        messages.success(request, "Your order has been placed successfully!")
        # Redirect to success page
        return redirect("order_success")

    return render(request, "cart/checkout.html", {"cart_items": cart_items, "total": total})

# Order success page
@login_required(login_url='login')
def order_success(request):
    return render(request, "cart/order_success.html")