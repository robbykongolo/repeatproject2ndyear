
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from .forms import SignUpForm

from .models import Product, Order, OrderItem, Wishlist

def home(request):
    return redirect('product_list')

def product_list(request):
    q = request.GET.get('q', '')
    products = Product.objects.all().select_related('category')
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
    paginator = Paginator(products, 8)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    return render(request, "store/product_list.html", {"products": products_page, "q": q})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "store/product_detail.html", {"product": product})

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Account created. Welcome!")
            return redirect("product_list")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignUpForm()
        return render(request, "store/signup.html", {"form": form})

@login_required
def cart_view(request):
    order, _ = Order.objects.get_or_create(user=request.user, is_paid=False)
    return render(request, "store/cart.html", {"order": order})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order, _ = Order.objects.get_or_create(user=request.user, is_paid=False)
    item, created = OrderItem.objects.get_or_create(order=order, product=product)
    if not created:
        item.quantity += 1
    item.save()
    messages.success(request, f"Added {product.name} to cart.")
    return redirect("cart")

@login_required
def decrement_from_cart(request, pk):
    order = get_object_or_404(Order, user=request.user, is_paid=False)
    item = get_object_or_404(OrderItem, order=order, product_id=pk)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect("cart")

@login_required
def remove_from_cart(request, pk):
    order = get_object_or_404(Order, user=request.user, is_paid=False)
    item = get_object_or_404(OrderItem, order=order, product_id=pk)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect("cart")

@login_required
def checkout(request):
    order = get_object_or_404(Order, user=request.user, is_paid=False)
    # Stripe integration placeholder - mark paid for demo
    if request.method == "POST":
        order.is_paid = True
        order.save()
        messages.success(request, "Payment successful (demo).")
        return redirect("order_history")
    return render(request, "store/checkout.html", {"order": order})

@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, "store/wishlist.html", {"wishlist": wishlist})

@login_required
def add_to_wishlist(request, pk):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, pk=pk)
    wishlist.products.add(product)
    messages.success(request, f"Added {product.name} to wishlist.")
    return redirect("wishlist")

@login_required
def remove_from_wishlist(request, pk):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.remove(pk)
    return redirect("wishlist")

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user, is_paid=True).order_by('-created_at')
    return render(request, "store/order_history.html", {"orders": orders})
