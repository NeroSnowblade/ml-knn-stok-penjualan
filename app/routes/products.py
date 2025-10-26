from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from .. import db
from ..models import Barang
from . import role_required


products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
@login_required
@role_required("admin")
def list_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = per_page if per_page in {5, 10, 25, 50} else 10

    pagination = Barang.query.order_by(Barang.nama.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "products/index.html",
        pagination=pagination,
        per_page=per_page,
        per_page_options=[5, 10, 25, 50],
    )


@products_bp.route("/create", methods=["POST"])
@login_required
@role_required("admin")
def create_product():
    name = request.form.get("nama", "").strip()
    ptype = request.form.get("tipe_barang", "").strip()
    stock = request.form.get("jumlah_stok", "0").strip()
    price = request.form.get("harga", "0").strip()

    if not name:
        flash("Nama produk wajib diisi.", "danger")
        return redirect(url_for("products.list_products"))
    if not ptype:
        flash("Tipe barang wajib diisi.", "danger")
        return redirect(url_for("products.list_products"))

    try:
        parsed_stock = int(stock)
        parsed_price = Decimal(price)
    except (ValueError, InvalidOperation):
        flash("Stok dan harga harus berupa angka.", "danger")
        return redirect(url_for("products.list_products"))

    product = Barang(nama=name, tipe_barang=ptype, jumlah_stok=parsed_stock, harga=parsed_price)
    db.session.add(product)
    db.session.commit()

    flash("Produk berhasil ditambahkan.", "success")
    return redirect(url_for("products.list_products"))


@products_bp.route("/<int:product_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_product(product_id: int):
    product = Barang.query.get_or_404(product_id)

    name = request.form.get("nama", "").strip()
    ptype = request.form.get("tipe_barang", "").strip()
    stock = request.form.get("jumlah_stok", "0").strip()
    price = request.form.get("harga", "0").strip()

    if not name:
        flash("Nama produk wajib diisi.", "danger")
        return redirect(url_for("products.list_products", page=request.args.get("page", 1)))
    if not ptype:
        flash("Tipe barang wajib diisi.", "danger")
        return redirect(url_for("products.list_products"))

    try:
        product.jumlah_stok = int(stock)
        product.harga = Decimal(price)
    except (ValueError, InvalidOperation):
        flash("Format stok atau harga tidak valid.", "danger")
        return redirect(url_for("products.list_products"))

    product.nama = name
    product.tipe_barang = ptype
    db.session.commit()

    flash("Produk berhasil diperbarui.", "success")
    return redirect(url_for("products.list_products"))


@products_bp.route("/<int:product_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_product(product_id: int):
    product = Barang.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash("Produk berhasil dihapus.", "success")
    return redirect(url_for("products.list_products"))
