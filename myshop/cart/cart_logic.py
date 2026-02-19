from .models import CartItem

def get_cart_items(user):
    items=CartItem.objects.filter(user=user)
    total=sum(item.subtotal() for item in items)
    return items, total