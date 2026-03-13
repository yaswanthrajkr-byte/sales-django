from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.db import transaction 

from .models import Product, Dealer, Order, Inventory
from .serializers import ProductSerializer, DealerSerializer, OrderSerializer, InventorySerializer


def home(request):
    return render(request, "index.html")


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class DealerViewSet(viewsets.ModelViewSet):
    queryset = Dealer.objects.all()
    serializer_class = DealerSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["dealer__name", "status"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """Confirm an order, validate and deduct stock from Inventory."""
        order = self.get_object()

        if order.status != "draft":
            return Response(
                {"status": [f"Cannot confirm order with status '{order.status}'"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():

               
                product_ids = [item.product.id for item in order.items.all()]
                if len(product_ids) != len(set(product_ids)):
                    return Response(
                        {
                            "items": [
                                "Each product can only be added once per order"
                            ]
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Validate inventory
                order.validate_inventory()

                for item in order.items.all():
                    product = item.product

                    try:
                        inventory = product.inventory
                    except Inventory.DoesNotExist:
                        return Response(
                            {"items": [f"No inventory record found for {product.name}"]},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    if inventory.quantity < item.quantity:
                        return Response(
                            {
                                "items": [
                                    f"Insufficient stock for {product.name}. "
                                    f"Requested: {item.quantity}, Available: {inventory.quantity}"
                                ]
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    inventory.quantity -= item.quantity
                    inventory.save()

                order.status = "confirmed"
                order.save()

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status == "delivered":
            return Response(
                {"status": ["Cannot delete an order with status 'delivered'"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                if order.status == "confirmed":
                    for item in order.items.all():
                        product = item.product
                        try:
                            inventory = product.inventory
                        except Inventory.DoesNotExist:
                            return Response(
                                {"items": [f"No inventory record found for {product.name}"]},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                        inventory.quantity += item.quantity
                        inventory.save()

                # actually delete
                super().destroy(request, *args, **kwargs)

            return Response(
                {"detail": "Deleted successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)   

    @action(detail=True, methods=["post"], url_path="deliver")
    def deliver(self, request, pk=None):
        """Mark an order as delivered."""
        order = self.get_object()

        if order.status != "confirmed":
            return Response(
                {"error": f"Cannot deliver order with status '{order.status}'. Order must be confirmed first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = "delivered"
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    lookup_field = "product_id"

    @action(detail=True, methods=["put"], url_path="adjust")
    def adjust_stock(self, request, product_id=None):
        """Manual stock adjustment for a product."""
        try:
            inventory = Inventory.objects.get(product_id=product_id)
        except Inventory.DoesNotExist:
            return Response(
                {"error": "Inventory not found for this product"},
                status=status.HTTP_404_NOT_FOUND
            )

        quantity = request.data.get("quantity")
        if quantity is None:
            return Response(
                {"error": "quantity field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError("Quantity cannot be negative")
        except (ValueError, TypeError):
            return Response(
                {"error": "quantity must be a non-negative integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        inventory.quantity = quantity
        inventory.save()

        serializer = self.get_serializer(inventory)
        return Response(serializer.data, status=status.HTTP_200_OK)