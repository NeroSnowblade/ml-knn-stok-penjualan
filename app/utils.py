from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
import random
import calendar
from typing import List, Optional

from sqlalchemy import func, inspect, text

from . import db
from .models import Barang, TransactionItem, Transaksi, User


@dataclass
class PredictionResult:
    product_id: int
    next_period: str
    predicted_quantity: int
    k: int
    neighbors: List[tuple]
    message: Optional[str] = None


def seed_default_admin() -> None:
    """Ensure an initial admin exists to unlock the application."""
    if User.query.filter_by(role="admin").first():
        return

    admin = User(username="admin", role="admin")
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()


def _add_one_month(base: datetime) -> datetime:
    year = base.year + (base.month // 12)
    month = 1 if base.month == 12 else base.month + 1
    if base.month == 12:
        year = base.year + 1
    return base.replace(year=year, month=month, day=1)


def prepare_monthly_sales(product_id: int) -> List[tuple]:
    results = (
        db.session.query(
            func.strftime("%Y-%m", Transaksi.tanggal_transaksi).label("period"),
            func.sum(TransactionItem.jumlah).label("total_qty"),
        )
        .join(Transaksi, TransactionItem.id_transaksi == Transaksi.id)
        .filter(TransactionItem.id_barang == product_id)
        .group_by("period")
        .order_by("period")
        .all()
    )
    cleaned: List[tuple] = []

    for row in results:
        try:
            period_date = datetime.strptime(f"{row.period}-01", "%Y-%m-%d")
        except ValueError:
            # Skip malformed rows rather than failing the prediction altogether.
            continue
        cleaned.append((period_date, int(row.total_qty or 0)))

    return cleaned


def predict_next_month_sales(product_id: int, k: int = 3) -> Optional[PredictionResult]:
    history = prepare_monthly_sales(product_id)
    if not history:
        return None

    ordered = sorted(history, key=lambda item: item[0])
    indexed = list(enumerate(qty for _, qty in ordered))

    if k <= 0:
        k = 1

    available = len(indexed)
    effective_k = min(k, available)

    target_index = available  # Next chronological slot

    def distance(point_index: int) -> int:
        return abs(point_index - target_index)

    neighbors = sorted(indexed, key=lambda it: distance(it[0]))[:effective_k]

    if not neighbors:
        return None

    predicted = round(sum(value for _, value in neighbors) / len(neighbors))

    last_period = ordered[-1][0]
    next_period_date = _add_one_month(last_period)
    period_label = next_period_date.strftime("%Y-%m")

    formatted_neighbors = [
        (
            ordered[idx][0].strftime("%Y-%m"),
            ordered[idx][1],
            distance(idx),
        )
        for idx, _ in neighbors
    ]

    return PredictionResult(
        product_id=product_id,
        next_period=period_label,
        predicted_quantity=max(0, predicted),
        k=effective_k,
        neighbors=formatted_neighbors,
        message=None if effective_k >= k else "Jumlah data historis kurang dari K yang diminta.",
    )


def ensure_tipe_barang_column(default_value: str = "Elektronik") -> None:
    """Ensure the 'tipe_barang' column exists in the 'barang' table and backfill values.

    This performs a lightweight runtime upgrade for SQLite and similar DBs.
    """
    engine = db.engine
    insp = inspect(engine)
    columns = {col["name"] for col in insp.get_columns("barang")}
    if "tipe_barang" not in columns:
        # Add the column; SQLite supports ADD COLUMN without constraints
        db.session.execute(text("ALTER TABLE barang ADD COLUMN tipe_barang VARCHAR(80)"))
        db.session.commit()
    # Backfill NULLs to a default value
    db.session.execute(text("UPDATE barang SET tipe_barang = :val WHERE tipe_barang IS NULL"), {"val": default_value})
    db.session.commit()


def seed_dummy_electronics_data(months: int = 12) -> int:
    """Seed electronic-themed products and random transactions over the last N months.

    Returns the number of transactions created. Skips if data already present.
    """
    ensure_tipe_barang_column()

    # Avoid duplicate seeding if transactions already exist
    if Transaksi.query.count() > 0:
        return 0

    # Define electronic products (name, category, price)
    specs = [
        ("Laptop Ultrabook 14\"", "Komputer", Decimal("12500000.00")),
        ("Laptop Gaming 15\"", "Komputer", Decimal("18500000.00")),
        ("PC Mini", "Komputer", Decimal("7500000.00")),
        ("Monitor 27\" 144Hz", "Aksesoris", Decimal("3500000.00")),
        ("Monitor 24\" IPS", "Aksesoris", Decimal("2200000.00")),
        ("Keyboard Mekanik", "Aksesoris", Decimal("750000.00")),
        ("Mouse Wireless", "Aksesoris", Decimal("250000.00")),
        ("Headset Gaming", "Audio", Decimal("950000.00")),
        ("Speaker Bluetooth", "Audio", Decimal("650000.00")),
        ("Smartphone 5G", "Gadget", Decimal("5500000.00")),
        ("Tablet 10\"", "Gadget", Decimal("4200000.00")),
        ("Smartwatch", "Gadget", Decimal("1800000.00")),
        ("Router WiFi 6", "Jaringan", Decimal("1200000.00")),
        ("Extender WiFi", "Jaringan", Decimal("450000.00")),
        ("SSD NVMe 1TB", "Storage", Decimal("1600000.00")),
        ("HDD 2TB", "Storage", Decimal("1100000.00")),
        ("Printer Inkjet", "Periferal", Decimal("1650000.00")),
        ("UPS 1000VA", "Periferal", Decimal("1350000.00")),
        ("Kamera Mirrorless", "Kamera", Decimal("7800000.00")),
        ("Lensa 50mm", "Kamera", Decimal("2200000.00")),
    ]

    # Create products if missing
    products: List[Barang] = []
    for name, category, price in specs:
        prod = Barang.query.filter_by(nama=name).first()
        if not prod:
            prod = Barang(nama=name, tipe_barang=category, harga=price, jumlah_stok=1000)
            db.session.add(prod)
        products.append(prod)
    db.session.commit()

    # Time range: last `months` full months up to current month inclusive
    today = date.today()
    # Determine first day of current month
    start_month = date(today.year, today.month, 1)
    # Go back (months-1) months
    year = start_month.year
    month = start_month.month
    for _ in range(months - 1):
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    first_period = date(year, month, 1)

    def iter_months(start: date, count: int):
        y, m = start.year, start.month
        for _ in range(count):
            yield y, m
            if m == 12:
                y, m = y + 1, 1
            else:
                y, m = y, m + 1

    tx_created = 0
    rng = random.Random(42)

    for y, m in iter_months(first_period, months):
        days_in_month = calendar.monthrange(y, m)[1]
        tx_count = rng.randint(18, 42)  # transactions per month
        for _ in range(tx_count):
            day = rng.randint(1, days_in_month)
            t_date = date(y, m, day)

            # Choose 1-4 distinct items
            item_count = rng.randint(1, 4)
            chosen = rng.sample(products, k=item_count)

            transaksi = Transaksi(tanggal_transaksi=t_date, total_harga=Decimal("0.00"))
            total = Decimal("0.00")
            for prod in chosen:
                qty = rng.randint(1, 5)
                # Cap quantity by available stock
                qty = min(qty, max(1, prod.jumlah_stok))
                harga = Decimal(prod.harga)
                transaksi.items.append(
                    TransactionItem(product=prod, jumlah=qty, harga=harga)
                )
                prod.jumlah_stok = max(0, int(prod.jumlah_stok) - qty)
                total += harga * qty

            transaksi.total_harga = total
            db.session.add(transaksi)
            tx_created += 1

        db.session.commit()

    return tx_created
