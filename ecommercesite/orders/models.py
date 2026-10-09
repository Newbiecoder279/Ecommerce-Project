from django.db import models
from products.models import Product

# Create your models here.

import uuid
from django.db import models
from products.models import Product


class Order(models.Model):
    full_name = models.CharField(max_length=250)
    email = models.EmailField()
    address = models.CharField(max_length=250)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    transaction_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    esewa_reference_id = models.CharField(
        max_length=100,
        blank=True,
    )

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def __str__(self):
        return f"Order {self.id}"
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="order_items", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveBigIntegerField(default=1)
    
    def get_cost(self):
        return self.price * self.quantity
