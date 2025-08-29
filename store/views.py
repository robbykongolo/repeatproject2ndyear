
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from .forms import SignUpForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from .models import Product, Order, OrderItem, Wishlist, Review
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


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
    reviews = product.reviews.select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(a=Avg('rating'))['a'] or 0

    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__is_paid=True,
            product=product,
        ).exists()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to review.")
            return redirect('login')

        if not can_review:
            messages.error(request, "You can only review items you've purchased.")
            return redirect('product_detail', pk=pk)

        rating = int(request.POST.get('rating', 0))
        comment = (request.POST.get('comment') or '').strip()
        if 1 <= rating <= 5:
            Review.objects.update_or_create(
                product=product, user=request.user,
                defaults={'rating': rating, 'comment': comment}
            )
            messages.success(request, "Thanks for your review!")
        else:
            messages.error(request, "Please choose a rating between 1 and 5.")
        return redirect('product_detail', pk=pk)

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "can_review": can_review,
    })


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
    order = Order.objects.filter(pk=order.pk).prefetch_related('items__product').get()
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
    return render(request, "store/checkout.html", {
        "order": order,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    })

@login_required
def create_checkout_session(request):
    if request.method != "POST":
        messages.error(request, "Invalid method.")
        return redirect("checkout")

    order = get_object_or_404(Order, user=request.user, is_paid=False)
    if not order.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    line_items = []
    for item in order.items.select_related('product'):
        line_items.append({
            "price_data": {
                "currency": "eur",               
                "product_data": {"name": item.product.name},
                "unit_amount": int(item.product.price * 100),
            },
            "quantity": item.quantity,
        })

    success_url = request.build_absolute_uri(
        reverse("payment_success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"

    cancel_url = request.build_absolute_uri(reverse("payment_cancel"))

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=request.user.email or None, 
    )

    order.stripe_checkout_session_id = session.id
    order.save()

    return redirect(session.url, code=303)

@login_required
def payment_success(request):
    messages.success(request, "Thanks! Your payment was successful.")
    return redirect("order_history")

@login_required
def payment_cancel(request):
    messages.info(request, "Payment cancelled. You can try again.")
    return redirect("cart")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except ValueError:
        return HttpResponse(status=400) 
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400) 

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        try:
            order = Order.objects.get(stripe_checkout_session_id=session_id)
        except Order.DoesNotExist:
            return HttpResponse(status=200) 

        if not order.is_paid:
            for item in order.items.select_related('product'):
                if hasattr(item.product, "stock"):
                    item.product.stock = max(0, item.product.stock - item.quantity)
                    item.product.save()

            order.is_paid = True
            order.save()

    return HttpResponse(status=200)


@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist = (Wishlist.objects
                .filter(pk=wishlist.pk)
                .prefetch_related('products__category')
                .get())
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
def move_wishlist_to_cart(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    order, _ = Order.objects.get_or_create(user=request.user, is_paid=False)

    if wishlist.products.exists():
        for product in wishlist.products.all():
            item, created = OrderItem.objects.get_or_create(order=order, product=product)
            if not created:
                item.quantity += 1
            item.save()

        wishlist.products.clear()
        messages.success(request, "All wishlist items were added to your cart.")
    else:
        messages.info(request, "Your wishlist is empty.")

    return redirect("cart")


@login_required
def order_history(request):
    orders = (
        Order.objects
        .filter(user=request.user, is_paid=True)
        .prefetch_related('items__product', 'items__product__category')
        .order_by('-created_at')
    )
    return render(request, "store/order_history.html", {"orders": orders})

@login_required
def reorder(request, order_id):
    if request.method != "POST":
        messages.error(request, "Invalid method.")
        return redirect("order_history")

    prev = get_object_or_404(Order, pk=order_id, user=request.user, is_paid=True)
    cart, _ = Order.objects.get_or_create(user=request.user, is_paid=False)

    for item in prev.items.select_related('product'):
        new_item, created = OrderItem.objects.get_or_create(order=cart, product=item.product)
        if created:
            new_item.quantity = item.quantity
        else:
            new_item.quantity += item.quantity
        new_item.save()

    messages.success(request, f"Reordered {prev.items.count()} item(s) into your cart.")
    return redirect("cart")



def logout_view(request):
    """Log the user out and always redirect to the product list with a flash."""
    logout(request)
    messages.info(request, "You have been logged out. See you soon!")
    return redirect("product_list")
