from django.urls import path
from . import views
from .views import download_bill
app_name='products'
urlpatterns=[
    path('home/',views.home,name='home'),
    path('product/<int:pk>/',views.product_detail,name='product_detail'),
    path('hello/', views.hello),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('signup/',views.signup, name="signup"),
    path('orders/', views.order_history, name='order_history'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path("orders/", views.order_history, name="order_history"),
    path('download-bill/<int:order_id>/',views.download_bill, name='download_bill'),
    path('bill-success/<int:order_id>/', views.bill_success, name='bill_success'),
]