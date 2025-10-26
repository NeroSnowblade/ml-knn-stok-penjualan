from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			if current_user.is_anonymous or current_user.role not in roles:
				flash("Anda tidak memiliki akses ke halaman tersebut.", "warning")
				return redirect(url_for("dashboard.index"))
			return func(*args, **kwargs)

		return wrapper

	return decorator
