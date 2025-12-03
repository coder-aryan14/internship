"""FastAPI application exposing the e-commerce platform."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import (
    Depends,
    FastAPI,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .platform import ECommercePlatform, bootstrap_platform
from .storage import PlatformStorage
from .users import AuthenticationError, User, require_admin
from .models import Order, Product, Category
from .payments import PaymentError, PaymentReceipt


storage = PlatformStorage()
platform: ECommercePlatform = bootstrap_platform(storage=storage)
app = FastAPI(title="Advanced E-Commerce Platform")
templates = Jinja2Templates(directory="ecommerce_system/templates")


def _extract_token(authorization: str = Header(...)) -> str:
    if authorization.lower().startswith("bearer "):
        return authorization[7:]
    return authorization


def get_current_user(token: str = Depends(_extract_token)) -> User:
    try:
        return platform.auth_service.resolve_user(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    require_admin(user)
    return user


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class CategoryCreateRequest(BaseModel):
    name: str
    description: str = ""


class ProductCreateRequest(BaseModel):
    name: str
    price: Decimal
    stock: int = Field(gt=0)
    category_id: str
    description: str = ""


class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class CheckoutRequest(BaseModel):
    payment_method: str


class PaymentConfirmationRequest(BaseModel):
    otp: Optional[str] = None
    transaction_id: Optional[str] = None
    delivered: Optional[bool] = None


@app.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    try:
        token = platform.auth_service.login(body.username, body.password)
        return LoginResponse(token=token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@app.post("/auth/password-reset/request")
def request_password_reset(username: str):
    try:
        token = platform.auth_service.request_password_reset(username)
        return {"reset_token": token}
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.post("/auth/password-reset/confirm")
def confirm_password_reset(token: str, new_password: str):
    try:
        platform.auth_service.reset_password(token, new_password)
        return {"status": "ok"}
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.get("/catalog/categories", response_model=List[Category])
def list_categories() -> List[Category]:
    return list(platform.categories.values())


@app.post("/catalog/categories", response_model=Category)
def create_category(body: CategoryCreateRequest, admin: User = Depends(get_admin_user)) -> Category:
    return platform.create_category(body.name, body.description, admin)


@app.delete("/catalog/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: str, admin: User = Depends(get_admin_user)) -> None:
    platform.delete_category(category_id, admin)


@app.get("/catalog/products", response_model=List[Product])
def list_products() -> List[Product]:
    return list(platform.products.values())


@app.post("/catalog/products", response_model=Product)
def add_product(body: ProductCreateRequest, admin: User = Depends(get_admin_user)) -> Product:
    return platform.add_product(
        name=body.name,
        price=body.price,
        stock=body.stock,
        category_id=body.category_id,
        acting_user=admin,
        description=body.description,
    )


@app.delete("/catalog/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: str, admin: User = Depends(get_admin_user)) -> None:
    platform.remove_product(product_id, admin)


@app.post("/cart/items")
def add_to_cart(body: CartItemRequest, user: User = Depends(get_current_user)):
    try:
        platform.add_to_cart(user.id, body.product_id, body.quantity)
        return {"status": "added"}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.delete("/cart/items")
def remove_from_cart(body: CartItemRequest, user: User = Depends(get_current_user)):
    platform.remove_from_cart(user.id, body.product_id, body.quantity)
    return {"status": "removed"}


@app.get("/cart")
def view_cart(user: User = Depends(get_current_user)):
    cart = platform.get_cart(user.id)
    return {
        "items": [
            {
                "product_id": item.product.id,
                "name": item.product.name,
                "quantity": item.quantity,
                "line_total": item.line_total,
            }
            for item in cart.items()
        ],
        "total": cart.total,
    }


@app.post("/checkout", response_model=Order)
def checkout(body: CheckoutRequest, user: User = Depends(get_current_user)) -> Order:
    try:
        return platform.checkout(user.id, body.payment_method)
    except (ValueError, PaymentError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.get("/payments/{reference}", response_model=PaymentReceipt)
def get_payment(reference: str, admin: User = Depends(get_admin_user)) -> PaymentReceipt:
    try:
        return platform.payment_processor.get_receipt(reference)
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@app.post("/payments/{reference}/confirm", response_model=Order)
def confirm_payment(reference: str, body: PaymentConfirmationRequest, admin: User = Depends(get_admin_user)):
    try:
        kwargs = body.dict(exclude_none=True)
        return platform.confirm_payment(reference, **kwargs)
    except (PaymentError, AuthenticationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.get("/orders", response_model=List[Order])
def list_orders(admin: User = Depends(get_admin_user)) -> List[Order]:
    return platform.list_orders(admin)


@app.get("/orders/me", response_model=List[Order])
def my_orders(user: User = Depends(get_current_user)) -> List[Order]:
    return [order for order in platform.orders.values() if order.user_id == user.id]


# ----------------------------
# HTML UI routes
# ----------------------------


def _user_from_cookie(request: Request) -> Optional[User]:
    token = request.cookies.get("session_token")
    if not token:
        return None
    try:
        return platform.auth_service.resolve_user(token)
    except AuthenticationError:
        return None


def _require_ui_user(request: Request) -> User:
    user = _user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    return user


@app.get("/", response_class=HTMLResponse)
def ui_store(request: Request):
    user = _user_from_cookie(request)
    products = list(platform.products.values())
    categories = list(platform.categories.values())
    return templates.TemplateResponse(
        "store.html",
        {
            "request": request,
            "title": "Store",
            "products": products,
            "categories": categories,
            "current_user": user,
            "message": None,
        },
    )


@app.get("/login", response_class=HTMLResponse)
def ui_login_page(request: Request):
    user = _user_from_cookie(request)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "title": "Login", "current_user": None, "message": None},
    )


@app.post("/login")
def ui_login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        token = platform.auth_service.login(username, password)
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "Login",
                "current_user": None,
                "message": str(exc),
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    resp.set_cookie("session_token", token, httponly=True)
    return resp


@app.post("/logout")
def ui_logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        platform.auth_service.logout(token)
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie("session_token")
    return resp


@app.post("/store/add-to-cart")
def ui_add_to_cart(
    request: Request,
    product_id: str = Form(...),
    quantity: int = Form(1),
):
    user = _require_ui_user(request)
    try:
        platform.add_to_cart(user.id, product_id, quantity)
    except Exception as exc:
        products = list(platform.products.values())
        categories = list(platform.categories.values())
        return templates.TemplateResponse(
            "store.html",
            {
                "request": request,
                "title": "Store",
                "products": products,
                "categories": categories,
                "current_user": user,
                "message": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url="/cart/view", status_code=status.HTTP_302_FOUND)


@app.get("/cart/view", response_class=HTMLResponse)
def ui_view_cart(request: Request):
    user = _require_ui_user(request)
    cart = platform.get_cart(user.id)
    items = [
        {
            "product_id": item.product.id,
            "name": item.product.name,
            "quantity": item.quantity,
            "line_total": item.line_total,
        }
        for item in cart.items()
    ]
    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "title": "Cart",
            "items": items,
            "total": cart.total,
            "current_user": user,
            "message": None,
        },
    )


@app.post("/cart/remove")
def ui_remove_from_cart(request: Request, product_id: str = Form(...)):
    user = _require_ui_user(request)
    platform.remove_from_cart(user.id, product_id, 1)
    return RedirectResponse(url="/cart/view", status_code=status.HTTP_302_FOUND)


@app.post("/cart/checkout", response_class=HTMLResponse)
def ui_checkout(request: Request, payment_method: str = Form(...)):
    user = _require_ui_user(request)
    try:
        order = platform.checkout(user.id, payment_method)
        receipt = None
        if order.payment_reference:
            try:
                receipt = platform.payment_processor.get_receipt(order.payment_reference)
            except PaymentError:
                receipt = None
        return templates.TemplateResponse(
            "checkout_result.html",
            {
                "request": request,
                "title": "Order placed",
                "order": order,
                "receipt": receipt,
                "current_user": user,
                "message": None,
            },
        )
    except (ValueError, PaymentError) as exc:
        cart = platform.get_cart(user.id)
        items = [
            {
                "product_id": item.product.id,
                "name": item.product.name,
                "quantity": item.quantity,
                "line_total": item.line_total,
            }
            for item in cart.items()
        ]
        return templates.TemplateResponse(
            "cart.html",
            {
                "request": request,
                "title": "Cart",
                "items": items,
                "total": cart.total,
                "current_user": user,
                "message": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@app.post("/payments/{reference}/confirm", response_class=HTMLResponse)
def ui_confirm_payment(request: Request, reference: str, otp: Optional[str] = Form(None)):
    user = _require_ui_user(request)
    try:
        kwargs = {}
        if otp:
            kwargs["otp"] = otp
        order = platform.confirm_payment(reference, **kwargs)
        receipt = platform.payment_processor.get_receipt(reference)
        return templates.TemplateResponse(
            "checkout_result.html",
            {
                "request": request,
                "title": "Payment confirmed",
                "order": order,
                "receipt": receipt,
                "current_user": user,
                "message": None,
            },
        )
    except (PaymentError, AuthenticationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@app.get("/admin", response_class=HTMLResponse)
def ui_admin(request: Request):
    user = _require_ui_user(request)
    require_admin(user)
    categories = list(platform.categories.values())
    products = list(platform.products.values())
    orders = platform.list_orders(user)
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "title": "Admin",
            "categories": categories,
            "products": products,
            "orders": orders,
            "current_user": user,
            "message": None,
        },
    )


@app.post("/admin/categories")
def ui_admin_add_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
):
    user = _require_ui_user(request)
    require_admin(user)
    platform.create_category(name, description, user)
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/products")
def ui_admin_add_product(
    request: Request,
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: str = Form(...),
    description: str = Form(""),
):
    user = _require_ui_user(request)
    require_admin(user)
    platform.add_product(
        name=name,
        price=Decimal(str(price)),
        stock=stock,
        category_id=category_id,
        acting_user=user,
        description=description,
    )
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.get("/orders/me/ui", response_class=HTMLResponse)
def ui_my_orders(request: Request):
    user = _require_ui_user(request)
    orders = [order for order in platform.orders.values() if order.user_id == user.id]
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "title": "My orders",
            "orders": orders,
            "current_user": user,
            "message": None,
        },
    )

