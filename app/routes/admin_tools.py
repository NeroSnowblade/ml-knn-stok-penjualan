from flask import Blueprint, flash, redirect, url_for
from flask_login import login_required

from .. import db
from ..utils import ensure_tipe_barang_column, seed_dummy_electronics_data
from . import role_required


admin_tools_bp = Blueprint("admin_tools", __name__, url_prefix="/admin")


@admin_tools_bp.route("/seed-dummy")
@login_required
@role_required("admin")
def seed_dummy():
    # Ensure schema upgrade first, then seed
    ensure_tipe_barang_column()
    created = seed_dummy_electronics_data(months=12)
    if created > 0:
        flash(f"Berhasil membuat {created} transaksi dummy selama 12 bulan beserta data barang elektronik.", "success")
    else:
        flash("Data sudah ada. Tidak ada data dummy baru yang dibuat.", "info")
    return redirect(url_for("reports.sales_report"))
