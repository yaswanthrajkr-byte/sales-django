from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Dealer(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

 

class Product(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("delivered", "Delivered"),
    ]
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    order_number = models.CharField(max_length=20, unique=True, editable=False)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):

        # Auto-generate order number
        if not self.order_number:
            today = timezone.now().strftime("%Y%m%d")

            last_order = Order.objects.filter(
                order_number__startswith=f"ORD-{today}"
            ).order_by("-order_number").first()

            if last_order:
                last_seq = int(last_order.order_number.split("-")[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1

            self.order_number = f"ORD-{today}-{str(new_seq).zfill(4)}"

        super().save(*args, **kwargs)

    def validate_inventory(self):
        """Validate that all order items have sufficient stock."""
        for item in self.items.all():
            try:
                inventory = Inventory.objects.get(product=item.product)
                if item.quantity > inventory.quantity:
                    raise ValidationError(
                        f"Insufficient stock for {item.product.name}. "
                        f"Requested: {item.quantity}, Available: {inventory.quantity}"
                    )
            except Inventory.DoesNotExist:
                raise ValidationError(
                    f"No inventory record found for {item.product.name}"
                )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # calculate line total
        self.line_total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_updates",
    )

    def __str__(self):
        return f"{self.product.name} - Stock: {self.quantity}"