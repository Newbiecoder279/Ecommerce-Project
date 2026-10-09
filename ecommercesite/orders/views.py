import requests
import base64
import json

from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET

from cart.models import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .utils import (
    generate_esewa_signature,
    verify_esewa_signature,
)


def order_create(request):
    cart_id = request.session.get("cart_id")
    cart = Cart.objects.filter(id=cart_id).first() if cart_id else None

    if not cart or not cart.items.exists():
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.save()

                for item in cart.items.select_related("product").all():
                    if not item.product.available:
                        form.add_error(
                            None,
                            f"{item.product.name} is no longer available."
                        )
                        transaction.set_rollback(True)
                        return render(
                            request,
                            "orders/order_create.html",
                            {"cart": cart, "form": form},
                        )

                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )

            # Build the eSewa payment form.
            amount = f"{order.get_total_cost():.2f}"
            transaction_uuid = str(order.transaction_uuid)
            product_code = settings.ESEWA_PRODUCT_CODE

            message = (
                f"total_amount={amount},"
                f"transaction_uuid={transaction_uuid},"
                f"product_code={product_code}"
            )

            signature = generate_esewa_signature(
                message,
                settings.ESEWA_SECRET_KEY,
            )

            form_data = {
                "amount": amount,
                "tax_amount": "0",
                "total_amount": amount,
                "transaction_uuid": transaction_uuid,
                "product_code": product_code,
                "product_service_charge": "0",
                "product_delivery_charge": "0",
                "success_url": request.build_absolute_uri(
                    reverse("orders:esewa_success")
                ),
                "failure_url": request.build_absolute_uri(
                    reverse("orders:esewa_failure")
                ),
                "signed_field_names": (
                    "total_amount,transaction_uuid,product_code"
                ),
                "signature": signature,
            }

            # Clear the cart only after the order is saved.
            cart.delete()
            request.session.pop("cart_id", None)

            return render(
                request,
                "orders/esewa_redirect.html",
                {
                    "payment_url": settings.ESEWA_PAYMENT_URL,
                    "form_data": form_data,
                },
            )
    else:
        form = OrderCreateForm()

    return render(
        request,
        "orders/order_create.html",
        {"cart": cart, "form": form},
    )


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(
        request,
        "orders/order_confirmation.html",
        {"order": order},
    )


@require_GET
def esewa_success(request):
    encoded_data = request.GET.get("data")

    if not encoded_data:
        return render(
            request,
            "orders/payment_result.html",
            {"message": "No payment response was received."},
        )

    try:
        decoded = base64.b64decode(
            encoded_data,
            validate=True,
        )
        data = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return render(
            request,
            "orders/payment_result.html",
            {"message": "The payment response could not be read."},
        )

    if not verify_esewa_signature(
        data,
        settings.ESEWA_SECRET_KEY,
    ):
        return render(
            request,
            "orders/payment_result.html",
            {"message": "Payment verification failed."},
        )

    transaction_uuid = data.get("transaction_uuid")

    order = get_object_or_404(
        Order,
        transaction_uuid=transaction_uuid,
    )

    expected_amount = f"{order.get_total_cost():.2f}"

    try:
        if (
            data.get("product_code") != settings.ESEWA_PRODUCT_CODE
            or Decimal(str(data.get("total_amount"))) != Decimal(expected_amount)
        ):
            raise ValueError("Payment details do not match.")

        # Verify the payment directly with eSewa.
        response = requests.get(
            settings.ESEWA_STATUS_URL,
            params={
                "product_code": settings.ESEWA_PRODUCT_CODE,
                "total_amount": expected_amount,
                "transaction_uuid": str(order.transaction_uuid),
            },
            timeout=15,
        )
        response.raise_for_status()
        status_data = response.json()

    except (ValueError, TypeError, requests.RequestException):
        return render(
            request,
            "orders/payment_result.html",
            {
                "message": (
                    "We could not confirm your payment yet. "
                    "Your order has not been marked as paid."
                ),
                "order": order,
            },
        )

    if status_data.get("status") != "COMPLETE":
        return render(
            request,
            "orders/payment_result.html",
            {
                "message": (
                    "Payment is not confirmed. "
                    "Please check your order status before retrying."
                ),
                "order": order,
            },
        )

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order.pk)

        # Idempotent: repeated callbacks won't undo a successful payment.
        if not order.paid:
            order.paid = True
            order.esewa_reference_id = (
                status_data.get("ref_id")
                or data.get("transaction_code")
                or ""
            )
            order.save(
                update_fields=["paid", "esewa_reference_id", "updated_at"]
            )

    return render(
        request,
        "orders/payment_result.html",
        {
            "message": "Payment successful!",
            "order": order,
        },
    )


@require_GET
def esewa_failure(request):
    return render(
        request,
        "orders/payment_result.html",
        {
            "message": (
                "The payment was cancelled or could not be completed. "
                "Your order remains unpaid."
            ),
        },
    )