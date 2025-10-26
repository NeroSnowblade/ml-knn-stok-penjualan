from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..models import User
from . import role_required


users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
@login_required
@role_required("admin")
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = per_page if per_page in {5, 10, 25, 50} else 10

    pagination = User.query.order_by(User.username.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "users/index.html",
        pagination=pagination,
        per_page=per_page,
        per_page_options=[5, 10, 25, 50],
    )


@users_bp.route("/create", methods=["POST"])
@login_required
@role_required("admin")
def create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "manager").strip()

    if not username or not password:
        flash("Username dan password wajib diisi.", "danger")
        return redirect(url_for("users.list_users"))

    if role not in {"admin", "manager"}:
        flash("Peran pengguna tidak valid.", "danger")
        return redirect(url_for("users.list_users"))

    if User.query.filter_by(username=username).first():
        flash("Username sudah digunakan.", "danger")
        return redirect(url_for("users.list_users"))

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Pengguna berhasil dibuat.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/update", methods=["POST"])
@login_required
@role_required("admin")
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)

    username = request.form.get("username", "").strip()
    role = request.form.get("role", "manager").strip()
    password = request.form.get("password", "")

    if not username:
        flash("Username wajib diisi.", "danger")
        return redirect(url_for("users.list_users"))

    if role not in {"admin", "manager"}:
        flash("Peran pengguna tidak valid.", "danger")
        return redirect(url_for("users.list_users"))

    existing = User.query.filter(User.id != user.id, User.username == username).first()
    if existing:
        flash("Username sudah digunakan pengguna lain.", "danger")
        return redirect(url_for("users.list_users"))

    user.username = username
    user.role = role
    if password:
        user.set_password(password)

    db.session.commit()
    flash("Pengguna berhasil diperbarui.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Anda tidak dapat menghapus akun Anda sendiri.", "warning")
        return redirect(url_for("users.list_users"))

    db.session.delete(user)
    db.session.commit()

    flash("Pengguna berhasil dihapus.", "success")
    return redirect(url_for("users.list_users"))
