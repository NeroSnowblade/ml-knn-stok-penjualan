from datetime import datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload

from .. import db
from ..models import Barang, TransactionItem, Transaksi
from . import role_required


transactions_bp = Blueprint("transactions", __name__, url_prefix="/transactions")


def _parse_items(form):
    product_ids = form.getlist("product_id[]")
    quantities = form.getlist("quantity[]")
    items = []
    for product_id, qty in zip(product_ids, quantities):
        try:
            items.append((int(product_id), int(qty)))
        except (TypeError, ValueError):
            continue
    return [item for item in items if item[0] > 0 and item[1] > 0]


def _restore_stock(transaction: Transaksi) -> None:
    for item in transaction.items:
        item.product.jumlah_stok += item.jumlah


def _build_transaction_items(transaction: Transaksi, items_payload):
    total = Decimal("0")
    transaction.items.clear()
    for product_id, qty in items_payload:
        product = Barang.query.get(product_id)
        if not product:
            continue
        if product.jumlah_stok < qty:
            raise ValueError(f"Stok {product.nama} tidak mencukupi.")

        product.jumlah_stok -= qty
        new_item = TransactionItem(
            product=product,
            jumlah=qty,
            harga=product.harga,
        )
        transaction.items.append(new_item)
        total += product.harga * qty
    transaction.total_harga = total


@transactions_bp.route("/")
@login_required
@role_required("admin")
def list_transactions():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = per_page if per_page in {5, 10, 25, 50} else 10

    pagination = (
        Transaksi.query.options(joinedload(Transaksi.items).joinedload(TransactionItem.product))
        .order_by(Transaksi.tanggal_transaksi.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "transactions/index.html",
        pagination=pagination,
        per_page=per_page,
        per_page_options=[5, 10, 25, 50],
    )


@transactions_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_transaction():
    products = Barang.query.order_by(Barang.nama.asc()).all()
    if request.method == "POST":
        date_raw = request.form.get("tanggal_transaksi")
        items_payload = _parse_items(request.form)

        if not items_payload:
            flash("Minimal satu item transaksi harus diisi.", "danger")
            return redirect(url_for("transactions.create_transaction"))

        try:
            transaction_date = (
                datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else datetime.utcnow().date()
            )
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")
            return redirect(url_for("transactions.create_transaction"))

        transaction = Transaksi(tanggal_transaksi=transaction_date)
        try:
            _build_transaction_items(transaction, items_payload)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for("transactions.create_transaction"))

        db.session.add(transaction)
        db.session.commit()
        flash("Transaksi berhasil ditambahkan.", "success")
        return redirect(url_for("transactions.list_transactions"))

    return render_template("transactions/form.html", products=products, transaction=None)


@transactions_bp.route("/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_transaction(transaction_id: int):
    transaction = Transaksi.query.options(joinedload(Transaksi.items)).get_or_404(transaction_id)
    products = Barang.query.order_by(Barang.nama.asc()).all()

    if request.method == "POST":
        date_raw = request.form.get("tanggal_transaksi")
        items_payload = _parse_items(request.form)

        if not items_payload:
            flash("Minimal satu item transaksi harus diisi.", "danger")
            return redirect(url_for("transactions.edit_transaction", transaction_id=transaction_id))

        try:
            transaction_date = (
                datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else datetime.utcnow().date()
            )
        except ValueError:
            flash("Format tanggal tidak valid.", "danger")
            return redirect(url_for("transactions.edit_transaction", transaction_id=transaction_id))

        _restore_stock(transaction)

        try:
            _build_transaction_items(transaction, items_payload)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for("transactions.edit_transaction", transaction_id=transaction_id))

        transaction.tanggal_transaksi = transaction_date
        db.session.commit()
        flash("Transaksi berhasil diperbarui.", "success")
        return redirect(url_for("transactions.list_transactions"))

    return render_template(
        "transactions/form.html",
        products=products,
        transaction=transaction,
    )


@transactions_bp.route("/<int:transaction_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_transaction(transaction_id: int):
    transaction = Transaksi.query.options(joinedload(Transaksi.items)).get_or_404(transaction_id)
    _restore_stock(transaction)
    db.session.delete(transaction)
    db.session.commit()

    flash("Transaksi berhasil dihapus.", "success")
    return redirect(url_for("transactions.list_transactions"))
