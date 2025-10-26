import math
from dataclasses import dataclass
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required
from sqlalchemy import and_, case, func

from ..models import Barang, TransactionItem, Transaksi
from ..utils import predict_next_month_sales
from .. import db
from . import role_required


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@dataclass
class SimplePagination:
    page: int
    per_page: int
    total: int
    items: list

    @property
    def pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page))

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def prev_num(self) -> int:
        return self.page - 1 if self.page > 1 else 1

    @property
    def next_num(self) -> int:
        return self.page + 1 if self.page < self.pages else self.pages


@reports_bp.route("/")
@login_required
@role_required("admin", "manager")
def sales_report():
    # Defaults
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)
    annual_year = request.args.get("annual_year", today.year, type=int)

    # Pagination controls for monthly and annual tables
    page_month = request.args.get("page_month", 1, type=int)
    per_page_month = request.args.get("per_page_month", 10, type=int)
    per_page_month = per_page_month if per_page_month in {5, 10, 25, 50} else 10

    page_year = request.args.get("page_year", 1, type=int)
    per_page_year = request.args.get("per_page_year", 10, type=int)
    per_page_year = per_page_year if per_page_year in {5, 10, 25, 50} else 10

    # Monthly window
    start_month = date(year, month, 1)
    if month == 12:
        start_next_month = date(year + 1, 1, 1)
    else:
        start_next_month = date(year, month + 1, 1)

    qty_sum_month = func.coalesce(
        func.sum(
            case(
                (and_(Transaksi.tanggal_transaksi >= start_month, Transaksi.tanggal_transaksi < start_next_month), TransactionItem.jumlah),
                else_=0,
            )
        ),
        0,
    )
    revenue_sum_month = func.coalesce(
        func.sum(
            case(
                (
                    and_(Transaksi.tanggal_transaksi >= start_month, Transaksi.tanggal_transaksi < start_next_month),
                    TransactionItem.jumlah * TransactionItem.harga,
                ),
                else_=0,
            )
        ),
        0,
    )

    monthly_query = (
        db.session.query(
            Barang.id.label("product_id"),
            Barang.nama.label("product_name"),
            Barang.tipe_barang.label("product_type"),
            qty_sum_month.label("total_qty"),
            revenue_sum_month.label("total_revenue"),
        )
        .outerjoin(TransactionItem, TransactionItem.id_barang == Barang.id)
        .outerjoin(Transaksi, TransactionItem.id_transaksi == Transaksi.id)
        .group_by(Barang.id, Barang.nama, Barang.tipe_barang)
        .order_by(Barang.nama.asc())
    )

    monthly_rows_all = [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "product_type": r.product_type,
            "total_qty": int(r.total_qty or 0),
            "total_revenue": float(r.total_revenue or 0),
        }
        for r in monthly_query.all()
    ]
    total_month = len(monthly_rows_all)
    start_idx = (page_month - 1) * per_page_month
    end_idx = start_idx + per_page_month
    monthly_rows = monthly_rows_all[start_idx:end_idx]
    monthly_pagination = SimplePagination(page=page_month, per_page=per_page_month, total=total_month, items=monthly_rows)

    # Annual window
    start_year = date(annual_year, 1, 1)
    start_next_year = date(annual_year + 1, 1, 1)

    qty_sum_year = func.coalesce(
        func.sum(
            case(
                (and_(Transaksi.tanggal_transaksi >= start_year, Transaksi.tanggal_transaksi < start_next_year), TransactionItem.jumlah),
                else_=0,
            )
        ),
        0,
    )
    revenue_sum_year = func.coalesce(
        func.sum(
            case(
                (
                    and_(Transaksi.tanggal_transaksi >= start_year, Transaksi.tanggal_transaksi < start_next_year),
                    TransactionItem.jumlah * TransactionItem.harga,
                ),
                else_=0,
            )
        ),
        0,
    )

    annual_query = (
        db.session.query(
            Barang.id.label("product_id"),
            Barang.nama.label("product_name"),
            Barang.tipe_barang.label("product_type"),
            qty_sum_year.label("total_qty"),
            revenue_sum_year.label("total_revenue"),
        )
        .outerjoin(TransactionItem, TransactionItem.id_barang == Barang.id)
        .outerjoin(Transaksi, TransactionItem.id_transaksi == Transaksi.id)
        .group_by(Barang.id, Barang.nama, Barang.tipe_barang)
        .order_by(Barang.nama.asc())
    )

    annual_rows_all = [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "product_type": r.product_type,
            "total_qty": int(r.total_qty or 0),
            "total_revenue": float(r.total_revenue or 0),
        }
        for r in annual_query.all()
    ]
    total_year = len(annual_rows_all)
    start_idx_y = (page_year - 1) * per_page_year
    end_idx_y = start_idx_y + per_page_year
    annual_rows = annual_rows_all[start_idx_y:end_idx_y]
    annual_pagination = SimplePagination(page=page_year, per_page=per_page_year, total=total_year, items=annual_rows)

    # Month navigation helpers
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # Year navigation helpers for annual table
    prev_annual_year = annual_year - 1
    next_annual_year = annual_year + 1

    prediction_neighbors = session.pop("prediction_neighbors", None)

    # Year options around current year for selects
    year_now = today.year
    year_options = list(range(year_now - 4, year_now + 2))

    return render_template(
        "reports/index.html",
        # Monthly context
        month=month,
        year=year,
        month_options=list(range(1, 13)),
        year_options=year_options,
        monthly_pagination=monthly_pagination,
        per_page_month=per_page_month,
        per_page_month_options=[5, 10, 25, 50],
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        # Annual context
        annual_year=annual_year,
        annual_pagination=annual_pagination,
        per_page_year=per_page_year,
        per_page_year_options=[5, 10, 25, 50],
        prev_annual_year=prev_annual_year,
        next_annual_year=next_annual_year,
        # Prediction extras
        prediction_product_id=request.args.get("prediction_product_id", type=int),
        prediction_qty=request.args.get("prediction_qty", type=int),
        prediction_period=request.args.get("prediction_period", default=""),
        prediction_k=request.args.get("prediction_k", type=int),
        prediction_neighbors=prediction_neighbors,
    )


@reports_bp.route("/predict", methods=["POST"])
@login_required
@role_required("admin", "manager")
def predict_sales():
    product_id = request.form.get("product_id", type=int)
    k = request.form.get("k", type=int) or 3
    # Preserve monthly filters when redirecting back
    month = request.form.get("month", type=int)
    year = request.form.get("year", type=int)

    if not product_id:
        flash("Produk tidak valid untuk prediksi.", "danger")
        return redirect(url_for("reports.sales_report"))

    result = predict_next_month_sales(product_id, k)
    if not result:
        flash("Data historis belum cukup untuk melakukan prediksi.", "warning")
        return redirect(url_for("reports.sales_report"))

    if result.message:
        flash(result.message, "warning")

    session["prediction_neighbors"] = result.neighbors

    return redirect(
        url_for(
            "reports.sales_report",
            prediction_product_id=result.product_id,
            prediction_qty=result.predicted_quantity,
            prediction_period=result.next_period,
            prediction_k=result.k,
            month=month,
            year=year,
        )
    )
