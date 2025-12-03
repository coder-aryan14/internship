"""Example usage of the e-commerce platform."""

from decimal import Decimal

from .platform import bootstrap_platform


def main() -> None:
    platform = bootstrap_platform()
    admin = platform.auth_service.get_user("admin")
    assert admin is not None

    # Admin manages catalog
    electronics = platform.create_category("Electronics", "Devices and gadgets", admin)
    groceries = platform.create_category("Groceries", "Daily essentials", admin)

    phone = platform.add_product(
        name="Smartphone X",
        price=Decimal("699.99"),
        stock=10,
        category_id=electronics.id,
        acting_user=admin,
    )
    rice = platform.add_product(
        name="Organic Rice 5kg",
        price=Decimal("12.50"),
        stock=50,
        category_id=groceries.id,
        acting_user=admin,
    )

    customer = platform.auth_service.get_user("alice")
    assert customer is not None

    # Customer shops
    platform.add_to_cart(customer.id, phone.id, quantity=1)
    platform.add_to_cart(customer.id, rice.id, quantity=2)

    upi_order = platform.checkout(user_id=customer.id, payment_method="upi")
    print("UPI order summary:", upi_order.summary())
    print("UPI order total:", upi_order.subtotal)
    print("UPI payment reference:", upi_order.payment_reference)

    # Demo a card checkout that requires OTP confirmation
    platform.add_to_cart(customer.id, phone.id, quantity=1)
    card_order = platform.checkout(user_id=customer.id, payment_method="card")
    print("Card order status:", card_order.status)
    if card_order.payment_reference:
        receipt = platform.payment_processor.get_receipt(card_order.payment_reference)
        otp_code = receipt.metadata.get("otp")
        if otp_code:
            platform.confirm_payment(card_order.payment_reference, otp=otp_code)
            print("Card order confirmed. Status:", card_order.status)
        else:
            print("No OTP required for this card transaction.")


if __name__ == "__main__":
    main()

