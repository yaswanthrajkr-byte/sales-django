from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, DealerViewSet, OrderViewSet, InventoryViewSet

router = DefaultRouter()

router.register("products", ProductViewSet)
router.register("dealers", DealerViewSet)
router.register("orders", OrderViewSet)
router.register("inventory", InventoryViewSet, basename="inventory")

urlpatterns = router.urls