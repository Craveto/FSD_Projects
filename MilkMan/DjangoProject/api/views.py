from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Admin, Category, Subscription, Customer, Product, SubscriptionBasketItem,
    SubscriptionDelivery, SubscriptionDeliveryItem,
    PaymentTransaction,
    Order, OrderItem, OrderPayment
)
from .serializers import (
    AdminSerializer, CategorySerializer, SubscriptionSerializer,
    CustomerSerializer, ProductSerializer, ProductDetailSerializer,
    CustomerDetailSerializer, PaymentTransactionSerializer,
    OrderSerializer, OrderPaymentSerializer, SubscriptionBasketItemSerializer,
    SubscriptionDeliverySerializer
)


def _resolve_admin_for_request(request):
    session_obj = getattr(request, "session", None)
    if session_obj is None and hasattr(request, "_request"):
        session_obj = getattr(request._request, "session", None)
    if not session_obj:
        return None

    auth_role = session_obj.get("auth_role")
    auth_user_id = session_obj.get("auth_user_id")
    if auth_role != "admin" or not auth_user_id:
        return None

    return Admin.objects.filter(admin_id=auth_user_id, is_active=True).first()


def _scoped_products_queryset(request):
    admin = _resolve_admin_for_request(request)
    if not admin:
        return Product.objects.all()
    if admin.role == "super_admin":
        return Product.objects.all()
    return Product.objects.filter(created_by=admin)


# ======================== ADMIN VIEWSET ========================
class AdminViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Admin model
    list: GET /api/admins/
    create: POST /api/admins/
    retrieve: GET /api/admins/{id}/
    update: PUT /api/admins/{id}/
    partial_update: PATCH /api/admins/{id}/
    destroy: DELETE /api/admins/{id}/
    """
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['created_at', 'role']
    filterset_fields = ['role', 'is_active']

    def get_queryset(self):
        admin = _resolve_admin_for_request(self.request)
        if admin:
            return Admin.objects.filter(admin_id=admin.admin_id)
        return Admin.objects.all()
    
    @action(detail=False, methods=['get'])
    def active_admins(self, request):
        """Get all active admins"""
        admins = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(admins, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a specific admin"""
        admin = self.get_object()
        admin.is_active = False
        admin.save()
        return Response({'status': 'Admin deactivated'})


# ======================== CATEGORY VIEWSET ========================
class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Category model
    list: GET /api/categories/
    create: POST /api/categories/
    retrieve: GET /api/categories/{id}/
    update: PUT /api/categories/{id}/
    partial_update: PATCH /api/categories/{id}/
    destroy: DELETE /api/categories/{id}/
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        admin = _resolve_admin_for_request(self.request)
        queryset = Category.objects.all()
        if admin:
            if admin.role == "super_admin":
                return queryset
            queryset = queryset.filter(owner_admin=admin)
        return queryset

    def perform_create(self, serializer):
        admin = _resolve_admin_for_request(self.request)
        serializer.save(owner_admin=admin)
    
    @action(detail=False, methods=['get'])
    def active_categories(self, request):
        """Get all active categories"""
        categories = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products_count(self, request, pk=None):
        """Get product count for a category"""
        category = self.get_object()
        count = _scoped_products_queryset(request).filter(category=category).count()
        return Response({'category': category.name, 'product_count': count})


# ======================== SUBSCRIPTION VIEWSET ========================
class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Subscription model
    list: GET /api/subscriptions/
    create: POST /api/subscriptions/
    retrieve: GET /api/subscriptions/{id}/
    update: PUT /api/subscriptions/{id}/
    partial_update: PATCH /api/subscriptions/{id}/
    destroy: DELETE /api/subscriptions/{id}/
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'duration_days']
    filterset_fields = ['billing_cycle', 'is_active']

    def get_queryset(self):
        admin = _resolve_admin_for_request(self.request)
        queryset = Subscription.objects.all()
        if admin:
            if admin.role == "super_admin":
                return queryset
            queryset = queryset.filter(owner_admin=admin)
        return queryset

    def perform_create(self, serializer):
        admin = _resolve_admin_for_request(self.request)
        serializer.save(owner_admin=admin)
    
    @action(detail=False, methods=['get'])
    def active_subscriptions(self, request):
        """Get all active subscription plans"""
        subscriptions = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_price_range(self, request):
        """Filter subscriptions by price range"""
        min_price = request.query_params.get('min_price', 0)
        max_price = request.query_params.get('max_price', 10000)
        subscriptions = self.get_queryset().filter(
            price__gte=min_price,
            price__lte=max_price
        )
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)


# ======================== CUSTOMER VIEWSET ========================
class CustomerViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Customer model
    list: GET /api/customers/
    create: POST /api/customers/
    retrieve: GET /api/customers/{id}/
    update: PUT /api/customers/{id}/
    partial_update: PATCH /api/customers/{id}/
    destroy: DELETE /api/customers/{id}/
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name', 'email', 'city']
    ordering_fields = ['created_at', 'status']
    filterset_fields = ['status', 'is_verified', 'subscription']

    def get_queryset(self):
        admin = _resolve_admin_for_request(self.request)
        queryset = Customer.objects.all()
        if admin:
            if admin.role == "super_admin":
                return queryset
            queryset = queryset.filter(owner_admin=admin)
        return queryset

    def perform_create(self, serializer):
        admin = _resolve_admin_for_request(self.request)
        serializer.save(owner_admin=admin)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return CustomerDetailSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['get'])
    def active_customers(self, request):
        """Get all active customers"""
        customers = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def verified_customers(self, request):
        """Get all verified customers"""
        customers = self.get_queryset().filter(is_verified=True)
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a customer"""
        customer = self.get_object()
        customer.is_verified = True
        customer.save()
        return Response({'status': 'Customer verified'})
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a customer"""
        customer = self.get_object()
        customer.status = 'suspended'
        customer.save()
        return Response({'status': 'Customer suspended'})
    
    @action(detail=True, methods=['post'])
    def reactivate(self, request, pk=None):
        """Reactivate a customer"""
        customer = self.get_object()
        customer.status = 'active'
        customer.save()
        return Response({'status': 'Customer reactivated'})


# ======================== PRODUCT VIEWSET ========================
class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Product model
    list: GET /api/products/
    create: POST /api/products/
    retrieve: GET /api/products/{id}/
    update: PUT /api/products/{id}/
    partial_update: PATCH /api/products/{id}/
    destroy: DELETE /api/products/{id}/
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'rating']
    filterset_fields = ['category', 'status', 'is_featured']

    def get_queryset(self):
        return _scoped_products_queryset(self.request)

    def perform_create(self, serializer):
        admin = _resolve_admin_for_request(self.request)
        serializer.save(created_by=admin)
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['get'])
    def active_products(self, request):
        """Get all active products"""
        products = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured_products(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True, status='active')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock (less than 10)"""
        threshold = request.query_params.get('threshold', 10)
        products = self.get_queryset().filter(quantity_in_stock__lt=threshold, status='active')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_price_range(self, request):
        """Filter products by price range"""
        min_price = request.query_params.get('min_price', 0)
        max_price = request.query_params.get('max_price', 10000)
        products = self.get_queryset().filter(
            price__gte=min_price,
            price__lte=max_price,
            status='active'
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get products by category"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': 'category_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        products = self.get_queryset().filter(category_id=category_id, status='active')
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


# ======================== DELIVERY VIEWSET (ADMIN) ========================
class SubscriptionDeliveryViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionDelivery.objects.all()
    serializer_class = SubscriptionDeliverySerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['customer__first_name', 'customer__last_name', 'items__product_name']
    ordering_fields = ['scheduled_for', 'status', 'updated_at']
    filterset_fields = ['status', 'scheduled_for', 'customer']

    def get_queryset(self):
        admin = _resolve_admin_for_request(self.request)
        queryset = SubscriptionDelivery.objects.all().prefetch_related('items')
        if not admin:
            # Delivery management is admin-only. Without an admin session, show nothing.
            return queryset.none()
        if admin.role == "super_admin":
            return queryset
        return queryset.filter(customer__owner_admin=admin)

    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        if not _resolve_admin_for_request(request):
            return Response({"error": "Admin authentication required"}, status=status.HTTP_403_FORBIDDEN)
        delivery = self.get_object()
        delivery.status = 'delivered'
        delivery.delivered_at = timezone.now()
        delivery.save(update_fields=['status', 'delivered_at'])
        return Response({"message": "Marked delivered", "delivery": self.get_serializer(delivery).data})

    @action(detail=True, methods=['post'])
    def mark_missed(self, request, pk=None):
        if not _resolve_admin_for_request(request):
            return Response({"error": "Admin authentication required"}, status=status.HTTP_403_FORBIDDEN)
        delivery = self.get_object()
        delivery.status = 'missed'
        delivery.delivered_at = None
        delivery.save(update_fields=['status', 'delivered_at'])
        return Response({"message": "Marked missed", "delivery": self.get_serializer(delivery).data})


# ======================== HELLO WORLD ENDPOINT ========================
@api_view(['GET'])
def hello_world(request):
    return Response({"message": "Hello, this is my first API!"})


def _admin_payload(admin):
    return {
        "id": admin.admin_id,
        "first_name": admin.first_name,
        "last_name": admin.last_name,
        "email": admin.email,
        "role": "admin",
        "admin_role": admin.role,
    }


def _customer_payload(customer):
    return {
        "id": customer.customer_id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "role": "user",
        "status": customer.status,
    }


def _persist_auth_session(request, role, user_id):
    try:
        request.session["auth_role"] = role
        request.session["auth_user_id"] = user_id
        return True
    except Exception:
        return False


@api_view(['POST'])
def auth_signup(request):
    role = request.data.get("role", "user")

    if role == "admin":
        required_fields = ["first_name", "last_name", "email", "phone", "username", "password"]
        missing = [field for field in required_fields if not request.data.get(field)]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminSerializer(data={
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "email": request.data.get("email"),
            "phone": request.data.get("phone"),
            "username": request.data.get("username"),
            "password": request.data.get("password"),
            "role": request.data.get("admin_role", "admin"),
            "is_active": True,
        })
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        session_persisted = _persist_auth_session(request, "admin", admin.admin_id)
        return Response(
            {"message": "Signup successful", "user": _admin_payload(admin), "session_persisted": session_persisted},
            status=status.HTTP_201_CREATED
        )

    required_fields = ["first_name", "last_name", "email", "phone", "password"]
    missing = [field for field in required_fields if not request.data.get(field)]
    if missing:
        return Response(
            {"error": f"Missing required fields: {', '.join(missing)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CustomerSerializer(data={
        "first_name": request.data.get("first_name"),
        "last_name": request.data.get("last_name"),
        "email": request.data.get("email"),
        "phone": request.data.get("phone"),
        "password": request.data.get("password"),
        "status": "active",
        "is_verified": False,
    })
    serializer.is_valid(raise_exception=True)
    customer = serializer.save()
    session_persisted = _persist_auth_session(request, "user", customer.customer_id)
    return Response(
        {"message": "Signup successful", "user": _customer_payload(customer), "session_persisted": session_persisted},
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
def auth_login(request):
    identifier = (request.data.get("identifier") or "").strip()
    password = request.data.get("password")

    if not identifier or not password:
        return Response(
            {"error": "identifier and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    admin = Admin.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
    if admin and admin.is_active and admin.check_password(password):
        session_persisted = _persist_auth_session(request, "admin", admin.admin_id)
        return Response({"message": "Login successful", "user": _admin_payload(admin), "session_persisted": session_persisted})

    customer = Customer.objects.filter(email__iexact=identifier).first()
    if customer and customer.status == "active" and customer.check_password(password):
        session_persisted = _persist_auth_session(request, "user", customer.customer_id)
        return Response({"message": "Login successful", "user": _customer_payload(customer), "session_persisted": session_persisted})

    return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def auth_me(request):
    auth_role = request.session.get("auth_role")
    auth_user_id = request.session.get("auth_user_id")

    if not auth_role or not auth_user_id:
        return Response({"user": None})

    if auth_role == "admin":
        admin = Admin.objects.filter(admin_id=auth_user_id, is_active=True).first()
        if not admin:
            try:
                request.session.flush()
            except Exception:
                pass
            return Response({"user": None})
        return Response({"user": _admin_payload(admin)})

    customer = Customer.objects.filter(customer_id=auth_user_id).first()
    if not customer:
        try:
            request.session.flush()
        except Exception:
            pass
        return Response({"user": None})
    return Response({"user": _customer_payload(customer)})


@api_view(['POST'])
def auth_logout(request):
    request.session.flush()
    return Response({"message": "Logout successful"})


def _resolve_customer_for_user_request(request):
    session_obj = getattr(request, "session", None)
    if session_obj is None and hasattr(request, "_request"):
        session_obj = getattr(request._request, "session", None)

    auth_role = session_obj.get("auth_role") if session_obj else None
    auth_user_id = session_obj.get("auth_user_id") if session_obj else None

    if auth_role == "user" and auth_user_id:
        return Customer.objects.filter(customer_id=auth_user_id).first()

    customer_id = request.query_params.get("customer_id") or request.data.get("customer_id")
    if not customer_id:
        return None

    return Customer.objects.filter(customer_id=customer_id).first()


def _validate_payment_details(payment_method, payload):
    method = (payment_method or '').lower()
    if method == 'cod':
        return True, None
    if method == 'card':
        card_number = (payload.get("card_number") or "").replace(" ", "")
        cvv = (payload.get("cvv") or "").strip()
        expiry = (payload.get("expiry") or "").strip()
        if len(card_number) < 12 or len(cvv) not in [3, 4] or len(expiry) < 4:
            return False, "Invalid card details"
        if card_number.endswith("0000"):
            return False, "Payment declined by gateway"
        return True, None
    if method == 'upi':
        upi_id = (payload.get("upi_id") or "").strip()
        if "@" not in upi_id:
            return False, "Invalid UPI ID"
        return True, None
    if method == 'netbanking':
        bank_name = (payload.get("bank_name") or "").strip()
        if not bank_name:
            return False, "Bank name is required"
        return True, None
    return False, "Unsupported payment method"


def _subscription_items_for_date(basket_items, subscription_start_date, target_date):
    day_items = []
    for basket_item in basket_items:
        if basket_item.frequency == 'daily':
            include = True
        elif basket_item.frequency == 'alternate':
            include = ((target_date - subscription_start_date).days % 2) == 0
        else:
            include = ((target_date - subscription_start_date).days % 7) == 0
        if include:
            day_items.append(basket_item)
    return day_items


def _rebuild_future_subscription_deliveries(customer, start_date=None):
    if not customer or not customer.subscription or not customer.subscription_start_date or not customer.subscription_end_date:
        return

    # Only rebuild for active subscription period.
    today = timezone.localdate()
    period_start = customer.subscription_start_date.date()
    period_end = customer.subscription_end_date.date()
    rebuild_start = max(period_start, today)
    if start_date:
        try:
            rebuild_start = max(rebuild_start, start_date)
        except Exception:
            pass

    if rebuild_start > period_end:
        return

    basket_items = list(
        SubscriptionBasketItem.objects.filter(customer=customer, is_active=True)
        .select_related('product')
        .order_by('product__name')
    )

    # If basket is empty, clear future scheduled deliveries.
    SubscriptionDelivery.objects.filter(
        customer=customer,
        scheduled_for__gte=rebuild_start,
        scheduled_for__lte=period_end,
        status='scheduled',
    ).delete()

    if not basket_items:
        return

    deliveries_to_create = []
    items_to_create = []

    current = rebuild_start
    while current <= period_end:
        todays = _subscription_items_for_date(basket_items, period_start, current)
        if todays:
            delivery = SubscriptionDelivery(
                customer=customer,
                subscription=customer.subscription,
                scheduled_for=current,
                status='scheduled',
            )
            deliveries_to_create.append(delivery)
        current = current + timedelta(days=1)

    if not deliveries_to_create:
        return

    # Bulk create deliveries, then attach items.
    SubscriptionDelivery.objects.bulk_create(deliveries_to_create, ignore_conflicts=True)
    created_deliveries = {
        d.scheduled_for: d
        for d in SubscriptionDelivery.objects.filter(
            customer=customer,
            scheduled_for__gte=rebuild_start,
            scheduled_for__lte=period_end,
            status='scheduled',
        )
    }

    current = rebuild_start
    while current <= period_end:
        delivery = created_deliveries.get(current)
        if delivery:
            todays = _subscription_items_for_date(basket_items, period_start, current)
            for basket_item in todays:
                items_to_create.append(SubscriptionDeliveryItem(
                    delivery=delivery,
                    product=basket_item.product,
                    product_name=basket_item.product.name,
                    quantity=basket_item.quantity,
                ))
        current = current + timedelta(days=1)

    if items_to_create:
        SubscriptionDeliveryItem.objects.bulk_create(items_to_create, ignore_conflicts=True)


@api_view(['GET'])
def user_dashboard_data(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    products = Product.objects.filter(status='active').order_by('-created_at')[:40]
    subscriptions = Subscription.objects.filter(is_active=True).order_by('price')
    recent_payments = PaymentTransaction.objects.filter(customer=customer).order_by('-created_at')[:10]
    basket_items = SubscriptionBasketItem.objects.filter(customer=customer, is_active=True).select_related('product').order_by('-updated_at')

    customer_subscription = None
    if customer.subscription:
        customer_subscription = {
            "subscription_id": customer.subscription.subscription_id,
            "name": customer.subscription.name,
            "subscription_start_date": customer.subscription_start_date,
            "subscription_end_date": customer.subscription_end_date,
        }

    return Response({
        "customer": {
            "customer_id": customer.customer_id,
            "name": f"{customer.first_name} {customer.last_name}".strip(),
            "email": customer.email,
            "status": customer.status,
            "current_subscription": customer_subscription,
        },
        "products": ProductSerializer(products, many=True).data,
        "subscriptions": SubscriptionSerializer(subscriptions, many=True).data,
        "recent_payments": PaymentTransactionSerializer(recent_payments, many=True).data,
        "subscription_basket": SubscriptionBasketItemSerializer(basket_items, many=True).data,
    })


@api_view(['GET', 'POST', 'DELETE'])
def user_subscription_basket(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        items = SubscriptionBasketItem.objects.filter(customer=customer, is_active=True).select_related('product').order_by('-updated_at')
        return Response(SubscriptionBasketItemSerializer(items, many=True).data)

    if not customer.subscription or not customer.subscription_end_date or customer.subscription_end_date < timezone.now():
        return Response({"error": "Active subscription required"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        product_id = request.query_params.get('product_id') or request.data.get('product_id')
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        SubscriptionBasketItem.objects.filter(customer=customer, product_id=product_id, is_active=True).update(is_active=False)
        _rebuild_future_subscription_deliveries(customer)
        return Response({"message": "Removed from subscription basket"})

    product_id = request.data.get('product')
    quantity = int(request.data.get('quantity') or 1)
    frequency = (request.data.get('frequency') or 'daily').lower()

    if not product_id:
        return Response({"error": "product is required"}, status=status.HTTP_400_BAD_REQUEST)

    product = Product.objects.filter(product_id=product_id, status='active').first()
    if not product:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    if not product.subscription_only:
        return Response({"error": "Product is not subscription-eligible"}, status=status.HTTP_400_BAD_REQUEST)

    if quantity < 1:
        return Response({"error": "quantity must be >= 1"}, status=status.HTTP_400_BAD_REQUEST)
    if frequency not in ['daily', 'alternate', 'weekly']:
        return Response({"error": "Invalid frequency"}, status=status.HTTP_400_BAD_REQUEST)

    item, _created = SubscriptionBasketItem.objects.update_or_create(
        customer=customer,
        product=product,
        is_active=True,
        defaults={'quantity': quantity, 'frequency': frequency},
    )
    _rebuild_future_subscription_deliveries(customer)
    return Response({"message": "Subscription basket updated", "item": SubscriptionBasketItemSerializer(item).data})


@api_view(['GET'])
def user_subscription_deliveries(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    days = int(request.query_params.get('days') or 7)
    days = min(max(days, 1), 31)

    if customer.subscription and customer.subscription_end_date and customer.subscription_end_date.date() >= timezone.localdate():
        # Ensure future schedule exists if basket is present.
        _rebuild_future_subscription_deliveries(customer)

    start = timezone.localdate()
    end = start + timedelta(days=days - 1)

    deliveries = (
        SubscriptionDelivery.objects.filter(customer=customer, scheduled_for__gte=start, scheduled_for__lte=end)
        .prefetch_related('items')
        .order_by('scheduled_for')
    )
    return Response({"deliveries": SubscriptionDeliverySerializer(deliveries, many=True).data})


@api_view(['POST'])
def user_subscribe(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    subscription_id = request.data.get("subscription_id")
    payment_method = (request.data.get("payment_method") or "card").lower()

    if not subscription_id:
        return Response({"error": "subscription_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    subscription = Subscription.objects.filter(subscription_id=subscription_id, is_active=True).first()
    if not subscription:
        return Response({"error": "Subscription plan not found or inactive"}, status=status.HTTP_404_NOT_FOUND)

    transaction = PaymentTransaction.objects.create(
        customer=customer,
        subscription=subscription,
        amount=subscription.price,
        payment_method=payment_method if payment_method in ['card', 'upi', 'netbanking'] else 'card',
        status='pending',
        currency='INR',
    )

    payment_success, failure_reason = _validate_payment_details(payment_method, request.data)

    if payment_success:
        now = timezone.now()
        transaction.status = 'success'
        transaction.paid_at = now
        transaction.failure_reason = None
        transaction.save(update_fields=['status', 'paid_at', 'failure_reason'])

        customer.subscription = subscription
        customer.subscription_start_date = now
        customer.subscription_end_date = now + timedelta(days=subscription.duration_days)
        customer.save(update_fields=['subscription', 'subscription_start_date', 'subscription_end_date'])

        _rebuild_future_subscription_deliveries(customer, start_date=customer.subscription_start_date.date())

        return Response({
            "message": "Payment successful and subscription activated",
            "payment": PaymentTransactionSerializer(transaction).data,
            "subscription": {
                "name": subscription.name,
                "start_date": customer.subscription_start_date,
                "end_date": customer.subscription_end_date,
            },
        }, status=status.HTTP_201_CREATED)

    transaction.status = 'failed'
    transaction.failure_reason = failure_reason
    transaction.save(update_fields=['status', 'failure_reason'])
    return Response({
        "error": "Payment failed",
        "reason": failure_reason,
        "payment": PaymentTransactionSerializer(transaction).data,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_payments(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    payments = PaymentTransaction.objects.filter(customer=customer).order_by('-created_at')
    return Response(PaymentTransactionSerializer(payments, many=True).data)


@api_view(['POST'])
def user_deactivate_subscription(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    if not customer.subscription:
        return Response({"error": "No active subscription found"}, status=status.HTTP_400_BAD_REQUEST)

    previous_subscription = customer.subscription.name
    customer.subscription = None
    customer.subscription_start_date = None
    customer.subscription_end_date = None
    customer.save(update_fields=['subscription', 'subscription_start_date', 'subscription_end_date'])

    # Remove any future scheduled deliveries; keep history (delivered/missed).
    SubscriptionDelivery.objects.filter(
        customer=customer,
        scheduled_for__gte=timezone.localdate(),
        status='scheduled',
    ).delete()

    return Response({
        "message": "Subscription deactivated successfully",
        "previous_subscription": previous_subscription,
    })


@api_view(['POST'])
def user_cart_checkout(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    cart_items = request.data.get("items") or []
    payment_method = (request.data.get("payment_method") or "card").lower()

    if not isinstance(cart_items, list) or len(cart_items) == 0:
        return Response({"error": "Cart items are required"}, status=status.HTTP_400_BAD_REQUEST)

    product_ids = [item.get('product_id') for item in cart_items if item.get('product_id')]
    products = Product.objects.filter(product_id__in=product_ids, status='active')
    product_map = {product.product_id: product for product in products}
    subscription_only_products = [product for product in products if getattr(product, 'subscription_only', False)]

    subtotal = 0
    normalized_items = []
    subscription_only_hits = []

    for item in cart_items:
        product_id = item.get('product_id')
        quantity = int(item.get('quantity') or 0)
        product = product_map.get(product_id)
        if not product or quantity <= 0:
            return Response({"error": "Invalid cart item payload"}, status=status.HTTP_400_BAD_REQUEST)

        if product.subscription_only:
            subscription_only_hits.append({
                "product_id": product.product_id,
                "name": product.name,
            })
            continue

        unit_price = float(product.price)
        line_total = unit_price * quantity
        subtotal += line_total
        normalized_items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total,
        })

    if subscription_only_hits:
        return Response(
            {
                "error": "Some items require subscription delivery",
                "subscription_only_items": subscription_only_hits,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    tax_amount = round(subtotal * 0.05, 2)
    total_amount = round(subtotal + tax_amount, 2)

    order = Order.objects.create(
        customer=customer,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency='INR',
        status='pending',
    )

    for line_item in normalized_items:
        OrderItem.objects.create(
            order=order,
            product=line_item['product'],
            quantity=line_item['quantity'],
            unit_price=line_item['unit_price'],
            line_total=line_item['line_total'],
        )

    payment = OrderPayment.objects.create(
        order=order,
        amount=total_amount,
        currency='INR',
        status='pending',
        payment_method=payment_method if payment_method in ['card', 'upi', 'netbanking', 'cod'] else 'card',
    )

    payment_success, failure_reason = _validate_payment_details(payment_method, request.data)
    if payment_success:
        now = timezone.now()
        if payment_method == 'cod':
            payment.status = 'pending'
            payment.paid_at = None
        else:
            payment.status = 'success'
            payment.paid_at = now
        payment.failure_reason = None
        payment.save(update_fields=['status', 'paid_at', 'failure_reason'])
        order.status = 'pending' if payment_method == 'cod' else 'paid'
        order.save(update_fields=['status'])
        return Response({
            "message": "Order placed" if payment_method == 'cod' else "Order payment successful",
            "order": OrderSerializer(order).data,
            "payment": OrderPaymentSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)

    payment.status = 'failed'
    payment.failure_reason = failure_reason
    payment.save(update_fields=['status', 'failure_reason'])
    order.status = 'failed'
    order.save(update_fields=['status'])
    return Response({
        "error": "Order payment failed",
        "reason": failure_reason,
        "order": OrderSerializer(order).data,
        "payment": OrderPaymentSerializer(payment).data,
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_orders(request):
    customer = _resolve_customer_for_user_request(request)
    if not customer:
        return Response({"error": "Valid customer not found"}, status=status.HTTP_400_BAD_REQUEST)

    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    return Response(OrderSerializer(orders, many=True).data)

