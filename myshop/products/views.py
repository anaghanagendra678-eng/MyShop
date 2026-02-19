from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from pathlib import Path
from .models import Product, Review, Order, OrderItem
from cart.models import CartItem   # ✅ import CartItem from cart app
from .forms import ReviewForm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ✅ Register a Unicode font that supports ₹
pdfmetrics.registerFont(
    TTFont('DejaVuSans', str(Path(__file__).resolve().parent / "static" / "fonts" / "DejaVuSans.ttf"))
)

# Home page – show all products
@login_required(login_url='login')
def home(request):
    products = Product.objects.all()
    return render(request, 'products/home.html', {'products': products})

# Product detail page – show product info and reviews
@login_required(login_url='login')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all()

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product   # ✅ link review to product
            review.user = request.user
            review.save()
            messages.success(request, "Your review has been submitted!")
            return redirect('product_detail', pk=product.pk)
    else:
        form = ReviewForm()

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form
    })

# Simple test view
def hello(request):
    return HttpResponse("Hello, this is the products app speaking!")

# Signup view
def signup(request):
    if request.method == "POST":
        username = request.POST["new_username"]
        email = request.POST["email"]
        password = request.POST["new_password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "products/login.html")

# Order history view
@login_required(login_url='login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'products/order_history.html', {'orders': orders})

# Add product to cart
@login_required(login_url='login')
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, f"{product.name} added to cart!")
    return redirect('cart')

# Cart view
@login_required(login_url='login')
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal for item in cart_items)
    return render(request, 'cart/cart.html', {'cart_items': cart_items, 'total': total})

# Checkout view
@login_required(login_url='login')
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.subtotal for item in cart_items)

    if request.method == "POST":
        address = request.POST.get("address")
        payment_method = request.POST.get("payment_method")

        order = Order.objects.create(
            user=request.user,
            total=total,
            address=address,
            payment_method=payment_method
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )

        cart_items.delete()
        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_success')

    return render(request, 'cart/checkout.html', {'cart_items': cart_items, 'total': total})

# Order success page
@login_required(login_url='login')
def order_success(request):
    return render(request, "cart/order_success.html")

# ✅ Downloadable PDF Bill
@login_required(login_url='login')
def download_bill(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)
    items = order.items.all()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{order_id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Logo
    logo_path = Path(__file__).resolve().parent / "static" / "products" / "myshoplogo.png"
    try:
        logo = Image(str(logo_path), width=120, height=120)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 20))
    except Exception:
        elements.append(Paragraph("<b>MyShop</b>", styles['Title']))
        elements.append(Spacer(1, 20))

    # Title
    title = Paragraph("<b>Order Receipt</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # ✅ Custom style with DejaVuSans
    custom_style = ParagraphStyle(
        'Custom',
        fontName='DejaVuSans',
        fontSize=12,
    )

    # Customer & Order Info
    info = Paragraph(
        f"Customer: {order.user.get_full_name() or order.user.username}<br/>"
        f"Order ID: {order.id}<br/>"
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        f"Payment Method: {order.payment_method}<br/>"
        f"Address: {order.address}<br/>"
        f"Total: ₹{order.total}",
        custom_style
    )
    elements.append(info)
    elements.append(Spacer(1, 20))

    # Table Data
    data = [["Product", "Quantity", "Subtotal"]]
    total = 0
    for item in items:
        subtotal = item.product.price * item.quantity
        data.append([item.product.name, str(item.quantity), f"₹{subtotal}"])
        total += subtotal

    data.append(["", "Total", f"₹{total}"])

    # Table with Unicode font
    table = Table(data, colWidths=[200, 100, 100])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),   # ✅ Unicode font
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('BACKGROUND', (0, 2), (-1, -2), colors.lavender),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    return response

def bill_success(request, order_id):
    return render(request, "products/bill_success.html", {"order_id": order_id})