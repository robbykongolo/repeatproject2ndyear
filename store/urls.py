from django.urls import path
from . import views
from django.contrib import messages
from django.shortcuts import resolve_url
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from .forms import SignUpForm

class CustomLoginView(LoginView):
    template_name = "store/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return response


urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('decrement/<int:pk>/', views.decrement_from_cart, name='decrement_from_cart'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='payment_success'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:pk>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path("wishlist/move-to-cart/", views.move_wishlist_to_cart, name="move_wishlist_to_cart"),

    path('orders/', views.order_history, name='order_history'),
    path("orders/reorder/<int:order_id>/", views.reorder, name="reorder"),


    path('signup/', views.signup, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name="store/password_change.html"), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name="store/password_change_done.html"), name='password_change_done'),

]
