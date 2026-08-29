"""
Idempotent demo-data seeder for MerchantGPT.

Creates one demo merchant ("Aurora Home Goods") with a realistic ~4-month
history of customers, products, orders, refunds, and abandoned carts --
deliberately shaped so every analytics feature has something real to show:
a high-refund product, a negative-margin product, a >65% cart abandonment
rate, a month-over-month revenue decline in the most recent month, and a
customer population spread across every RFM segment (including some who
are overdue enough to register as churn risks).

Run with: python -m scripts.seed   (from backend/, with the venv active and
DATABASE_URL_SYNC pointed at a real, non-production database).
"""

import random
from datetime import date, datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
import app.models  # noqa: F401 -- registers all models before create_all
from app.models import Merchant, User, Customer, Product, Order, OrderItem, OrderStatus, Cart, CartItem, CartStatus, Refund

settings = get_settings()
fake = Faker()
Faker.seed(42)
random.seed(42)

DEMO_MERCHANT_NAME = "Aurora Home Goods"
DEMO_USER_EMAIL = "demo@aurorahome.example"
DEMO_USER_PASSWORD = "Demo@12345"

PRODUCT_CATALOG = [
    # (name, category, price, cost)
    ("Ceramic Table Lamp", "Lighting", 58.00, 24.00),
    ("Linen Throw Pillow", "Textiles", 32.00, 11.00),
    ("Woven Storage Basket", "Storage", 44.00, 19.00),
    ("Marble Coasters (Set of 4)", "Accessories", 26.00, 9.00),
    ("Brass Wall Sconce", "Lighting", 76.00, 33.00),
    ("Cotton Waffle Throw Blanket", "Textiles", 48.00, 20.00),
    ("Rattan Pendant Light", "Lighting", 92.00, 41.00),
    ("Ceramic Planter (Medium)", "Decor", 28.00, 10.00),
    ("Oak Cutting Board", "Kitchen", 38.00, 16.00),
    ("Glass Carafe Set", "Kitchen", 34.00, 14.00),
    ("Wool Area Rug 5x7", "Textiles", 210.00, 95.00),
    ("Bamboo Bath Mat", "Bath", 22.00, 15.50),  # thin margin -- for the leak demo
    ("Recycled Glass Vase", "Decor", 30.00, 12.00),
    ("Linen Napkin Set", "Textiles", 24.00, 9.00),
    ("Cast Iron Trivet", "Kitchen", 18.00, 7.00),
    ("Seagrass Wall Mirror", "Decor", 64.00, 27.00),
    ("Stoneware Dinner Set", "Kitchen", 88.00, 38.00),
    ("Faux Fur Throw", "Textiles", 52.00, 21.00),
    ("Terracotta Plant Pot Trio", "Decor", 36.00, 14.00),
    ("Woven Placemats (Set of 4)", "Textiles", 20.00, 8.00),
    ("Amber Glass Pendant Light", "Lighting", 84.00, 36.00),
    ("Cork Yoga Mat", "Wellness", 40.00, 21.00),
    ("Scented Soy Candle", "Decor", 19.00, 6.00),
    ("Bamboo Utensil Set", "Kitchen", 21.00, 8.00),
    ("Linen Duvet Cover", "Textiles", 118.00, 52.00),
]

# One deliberately problematic product for the refund-leak demo (returns spike
# because of an inaccurate size listing -- a realistic, fixable cause).
LEAKY_PRODUCT_NAME = "Wool Area Rug 5x7"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def get_sync_engine():
    return create_engine(settings.database_url_sync, echo=False)


def seed(session: Session) -> None:
    existing = session.query(Merchant).filter(Merchant.name == DEMO_MERCHANT_NAME).first()
    if existing:
        print(f"Demo merchant '{DEMO_MERCHANT_NAME}' already exists -- nothing to seed.")
        return

    merchant = Merchant(name=DEMO_MERCHANT_NAME, industry="Home Goods & Decor", currency="USD")
    session.add(merchant)
    session.flush()

    user = User(
        merchant_id=merchant.id,
        name="Jordan Lee",
        email=DEMO_USER_EMAIL,
        password_hash=hash_password(DEMO_USER_PASSWORD),
        role="owner",
    )
    session.add(user)

    products = []
    for name, category, price, cost in PRODUCT_CATALOG:
        p = Product(merchant_id=merchant.id, name=name, sku=fake.bothify("SKU-####??").upper(), category=category, price=price, cost=cost)
        session.add(p)
        products.append(p)
    session.flush()

    leaky_product = next(p for p in products if p.name == LEAKY_PRODUCT_NAME)

    # --- Customers, spread across recency/frequency/monetary so every RFM
    # segment and churn-risk tier has real members to show. --------------
    customers = []
    NUM_CUSTOMERS = 180
    for _ in range(NUM_CUSTOMERS):
        c = Customer(merchant_id=merchant.id, name=fake.name(), email=fake.unique.email())
        session.add(c)
        customers.append(c)
    session.flush()

    # Assign each customer an archetype so the population has real structure
    # rather than uniform noise.
    archetypes = (
        ["champion"] * 15
        + ["loyal"] * 25
        + ["big_spender"] * 12
        + ["at_risk"] * 20
        + ["new"] * 30
        + ["lost"] * 25
        + ["regular"] * (NUM_CUSTOMERS - 127)
    )
    random.shuffle(archetypes)

    order_count = 0
    refund_count = 0
    today = date.today()

    for customer, archetype in zip(customers, archetypes):
        if archetype == "champion":
            n_orders = random.randint(8, 14)
            span_days = random.randint(90, 110)
            last_order_days_ago = random.randint(1, 5)
            price_bias = 1.3
        elif archetype == "loyal":
            n_orders = random.randint(5, 8)
            span_days = random.randint(80, 110)
            last_order_days_ago = random.randint(2, 15)
            price_bias = 1.0
        elif archetype == "big_spender":
            n_orders = random.randint(2, 4)
            span_days = random.randint(60, 100)
            last_order_days_ago = random.randint(10, 30)
            price_bias = 2.2
        elif archetype == "at_risk":
            n_orders = random.randint(3, 6)
            span_days = random.randint(60, 100)
            last_order_days_ago = random.randint(70, 150)  # overdue -> churn risk
            price_bias = 1.0
        elif archetype == "new":
            n_orders = 1
            span_days = 0
            last_order_days_ago = random.randint(1, 12)
            price_bias = 0.9
        elif archetype == "lost":
            n_orders = random.randint(1, 2)
            span_days = random.randint(0, 20)
            last_order_days_ago = random.randint(180, 340)
            price_bias = 0.8
        else:  # regular
            n_orders = random.randint(2, 4)
            span_days = random.randint(40, 90)
            last_order_days_ago = random.randint(20, 60)
            price_bias = 1.0

        last_order_date = today - timedelta(days=last_order_days_ago)
        if n_orders > 1:
            order_dates = sorted(
                last_order_date - timedelta(days=int(span_days * i / (n_orders - 1))) for i in range(n_orders)
            )
        else:
            order_dates = [last_order_date]

        customer.first_order_at = order_dates[0]

        for i, order_date in enumerate(order_dates):
            n_items = random.randint(1, 3)
            chosen_products = random.sample(products, n_items)
            # Bias toward the leaky product occasionally so it accumulates enough
            # orders to trigger the refund-rate detector.
            if random.random() < 0.12 and leaky_product not in chosen_products:
                chosen_products[0] = leaky_product

            order_dt = datetime.combine(order_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                hours=random.randint(8, 21)
            )

            # Deliberate revenue dip in the most recent ~30 days: skip roughly a
            # third of what would otherwise be this month's orders.
            if (today - order_date).days < 30 and random.random() < 0.35:
                continue

            order_total = 0.0
            order = Order(merchant_id=merchant.id, customer_id=customer.id, status=OrderStatus.COMPLETED, total_amount=0, created_at=order_dt)
            session.add(order)
            session.flush()

            for product in chosen_products:
                qty = random.randint(1, 2)
                unit_price = round(product.price * price_bias * random.uniform(0.95, 1.05), 2)
                session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=unit_price))
                order_total += qty * unit_price

            order.total_amount = round(order_total, 2)
            order_count += 1

            # Refunds: the leaky product refunds ~35% of the time; everything
            # else refunds rarely (a healthy baseline rate).
            refund_chance = 0.35 if any(p.id == leaky_product.id for p in chosen_products) else 0.04
            if random.random() < refund_chance:
                refund_amount = round(order_total * random.uniform(0.5, 1.0), 2)
                order.status = OrderStatus.PARTIALLY_REFUNDED if refund_amount < order_total else OrderStatus.REFUNDED
                session.add(
                    Refund(
                        merchant_id=merchant.id,
                        order_id=order.id,
                        amount=refund_amount,
                        reason=random.choice(["Wrong size", "Item damaged in transit", "Not as described", "Changed mind"]),
                        created_at=order_dt + timedelta(days=random.randint(1, 10)),
                    )
                )
                refund_count += 1

    # --- Abandoned carts: deliberately high abandonment rate (~70%). ----
    cart_count = 0
    for customer in random.sample(customers, 90):
        n_items = random.randint(1, 3)
        chosen_products = random.sample(products, n_items)
        cart_total = round(sum(p.price * random.randint(1, 2) for p in chosen_products), 2)
        created_at = now_utc() - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))

        roll = random.random()
        if roll < 0.70:
            status = CartStatus.ABANDONED
            abandoned_at = created_at + timedelta(hours=random.randint(1, 4))
        elif roll < 0.85:
            status = CartStatus.CONVERTED
            abandoned_at = None
        else:
            status = CartStatus.RECOVERED
            abandoned_at = created_at + timedelta(hours=random.randint(1, 4))

        cart = Cart(merchant_id=merchant.id, customer_id=customer.id, status=status, total_amount=cart_total, created_at=created_at, abandoned_at=abandoned_at)
        session.add(cart)
        session.flush()
        for product in chosen_products:
            session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=random.randint(1, 2), unit_price=product.price))
        cart_count += 1

    session.commit()
    print(f"Seed complete: {len(customers)} customers, {len(products)} products, {order_count} orders, {refund_count} refunds, {cart_count} carts.")
    print(f"Demo login -> email: {DEMO_USER_EMAIL}  password: {DEMO_USER_PASSWORD}")


def main() -> None:
    engine = get_sync_engine()
    with engine.begin() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except DBAPIError:
            # Same reasoning as app/main.py's lifespan handler: on most managed
            # Postgres hosts the app role can't run CREATE EXTENSION itself, so
            # assume an admin already enabled pgvector and move on.
            conn.rollback()
            print(
                "Warning: could not run CREATE EXTENSION vector (likely insufficient "
                "privilege on this role) -- assuming pgvector is already enabled."
            )
        Base.metadata.create_all(conn)

    with Session(engine) as session:
        seed(session)


if __name__ == "__main__":
    main()
