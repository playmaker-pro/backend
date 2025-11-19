from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from api.views import EndpointView
from payments.api.serializers import NewTransactionSerializer
from payments.providers.errors import TransactionError
from payments.services import TransactionService
from premium.api.serializers import PremiumProfileProductSerializer, ProductSerializer
from premium.models import PremiumType, Product


class ProductInfoView(EndpointView):
    queryset = Product.objects.filter(visible=True)
    serializer_class = ProductSerializer
    authentication_classes = []
    permission_classes = []

    def list_inquiry_products(self, request: Request) -> Response:
        queryset = self.get_queryset().filter(ref=Product.ProductReference.INQUIRIES)
        return Response(self.serializer_class(queryset, many=True).data)

    def get_premium_products(self, request: Request) -> Response:
        obj = self.get_queryset().filter(ref=Product.ProductReference.PREMIUM)
        return Response(self.serializer_class(obj, many=True).data)


class ProductView(EndpointView):
    queryset = Product.objects.all()
    serializer_class = NewTransactionSerializer

    def create_transaction(self, request: Request, product_id: int) -> Response:
        product: Product = get_object_or_404(Product, pk=product_id)

        if not product.visible:
            return Response(
                "You are not allowed to create transaction for this product.",
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            product.can_user_buy(request.user)
        except PermissionError as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        transaction_service = TransactionService.create_new_transaction_object(
            user=request.user, product=product
        )

        try:
            transaction = transaction_service.handle()
        except TransactionError:
            return Response(
                "Something went wrong. Try again later.",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = self.serializer_class(transaction)
        return Response(serializer.data)

    def activate_test_premium_product(self, request: Request) -> Response:
        profile = request.user.profile
        profile.ensure_premium_products_exist()

        if profile.premium_products.trial_tested:
            return Response(
                "You have already tested the premium product.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.setup_premium_profile(PremiumType.TRIAL)
        return Response(status=status.HTTP_200_OK)
