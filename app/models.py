from datetime import datetime
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)


class Barang(db.Model):
    __tablename__ = "barang"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(120), nullable=False)
    jumlah_stok = db.Column(db.Integer, nullable=False, default=0)
    harga = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tipe_barang = db.Column(db.String(80), nullable=False, default="Elektronik")

    transaksi_items = db.relationship("TransactionItem", back_populates="product")


class Transaksi(db.Model):
    __tablename__ = "transaksi"

    id = db.Column(db.Integer, primary_key=True)
    tanggal_transaksi = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    total_harga = db.Column(db.Numeric(14, 2), nullable=False, default=Decimal("0.00"))

    items = db.relationship(
        "TransactionItem",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )


class TransactionItem(db.Model):
    __tablename__ = "itemTransaksi"

    id = db.Column(db.Integer, primary_key=True)
    id_transaksi = db.Column(db.Integer, db.ForeignKey("transaksi.id"), nullable=False)
    id_barang = db.Column(db.Integer, db.ForeignKey("barang.id"), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False, default=0)
    harga = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    transaction = db.relationship("Transaksi", back_populates="items")
    product = db.relationship("Barang", back_populates="transaksi_items")
