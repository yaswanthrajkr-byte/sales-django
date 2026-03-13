from rest_framework import serializers
from .models import Dealer, Product, Order, OrderItem, Inventory


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "dealer", "dealer_name", "items", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_items(self, items):
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Each product can only be added once per order"
            )
        return items

    def create(self, validated_data):

        items_data = validated_data.pop("items")

        order = Order.objects.create(**validated_data)

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"]
            )

        return order

    def update(self, instance, validated_data):

        
        if instance.status in ["confirmed", "delivered"]:
            raise serializers.ValidationError(
                f"Cannot edit order with status '{instance.status}'"
            )

        items_data = validated_data.pop("items", None)

        # update dealer if provided
        instance.dealer = validated_data.get("dealer", instance.dealer)
        instance.status = validated_data.get("status", instance.status)
        instance.save()

        if items_data is not None:

           
            instance.items.all().delete()

          
            for item in items_data:
                OrderItem.objects.create(
                    order=instance,
                    product=item["product"],
                    quantity=item["quantity"]
                )

        return instance


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "product", "product_name", "product_code", "product_price", "quantity", "updated_at"]