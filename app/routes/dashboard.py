import json
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from ..models import Barang, TransactionItem, Transaksi
from .. import db


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    monthly_totals = (
        db.session.query(
            func.strftime("%Y-%m", Transaksi.tanggal_transaksi).label("period"),
            func.sum(TransactionItem.jumlah).label("total_qty"),
            func.sum(TransactionItem.jumlah * TransactionItem.harga).label("total_revenue"),
        )
        .join(Transaksi, TransactionItem.id_transaksi == Transaksi.id)
        .group_by("period")
        .order_by("period")
        .all()
    )

    chart_labels = [row.period for row in monthly_totals]
    chart_qty = [int(row.total_qty or 0) for row in monthly_totals]
    chart_revenue = [float(row.total_revenue or Decimal("0")) for row in monthly_totals]

    total_products = Barang.query.count()
    total_transactions = Transaksi.query.count()
    total_revenue = (
        db.session.query(func.sum(TransactionItem.jumlah * TransactionItem.harga)).scalar()
        or 0
    )

    return render_template(
        "dashboard.html",
        total_products=total_products,
        total_transactions=total_transactions,
        total_revenue=float(total_revenue),
        chart_labels=json.dumps(chart_labels),
        chart_qty=json.dumps(chart_qty),
        chart_revenue=json.dumps(chart_revenue),
    )
