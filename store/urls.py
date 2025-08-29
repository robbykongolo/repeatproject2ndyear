
from django.urls import path
from django.contrib import messages
from django.shortcuts import resolve_url
from django.contrib.auth.views import  LoginView, LogoutView

from . import views
from .forms import SignUpForm

class CustomLoginView(LoginView):
    template_name = "store/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return response

class CustomLogoutView(LogoutView):
    next_page = "product_list"
    http_method_names = ["get", "post"]

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "You have been logged out. See you soon!")
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        return resolve_url(self.next_page)

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('decrement/<int:pk>/', views.decrement_from_cart, name='decrement_from_cart'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:pk>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('orders/', views.order_history, name='order_history'),

    path('signup/', views.signup, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

]
