import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import engine  # noqa: E402
from app.services.synthetic import load_synthetic_packages  # noqa: E402


def main() -> None:
    packages = load_synthetic_packages()
    if not packages:
        raise SystemExit("No hay paquetes sintéticos para sembrar")

    database_url = get_settings().database_url
    if not database_url.startswith("postgresql"):
        raise SystemExit("El seed solo soporta PostgreSQL; revisa DATABASE_URL")

    with engine.begin() as connection:
        table = connection.execute(text("SELECT to_regclass('tour_package')")).scalar()
        if not table:
            print("La tabla tour_package no existe en esta base de datos; se omite el seed.")
            return

        inserted = skipped = 0
        for package in packages:
            coded = connection.execute(
                text("SELECT 1 FROM tour_package WHERE code = :code"),
                {"code": package["code"]},
            ).first()
            if coded:
                skipped += 1
                continue
            connection.execute(
                text(
                    "INSERT INTO tour_package (code, title, destination, country, "
                    "description, category, duration_days, base_price, currency, "
                    "max_travelers, cancel_days_before, cancel_refund_percent, rating, "
                    "active) VALUES (:code, :title, :destination, :country, :description, "
                    ":category, :duration_days, :base_price, :currency, :max_travelers, "
                    ":cancel_days_before, :cancel_refund_percent, :rating, TRUE)"
                ),
                {
                    "code": package["code"],
                    "title": package["title"],
                    "destination": package["destination"],
                    "country": package["country"],
                    "description": package["description"],
                    "category": package["category"],
                    "duration_days": package["durationDays"],
                    "base_price": package["basePrice"],
                    "currency": package["currency"],
                    "max_travelers": 8,
                    "cancel_days_before": 15,
                    "cancel_refund_percent": 100,
                    "rating": package["rating"],
                },
            )
            package_id = connection.execute(
                text("SELECT id FROM tour_package WHERE code = :code"),
                {"code": package["code"]},
            ).scalar()
            first_date = min(package["startDates"])
            connection.execute(
                text(
                    "INSERT INTO tour_package_start_date (package_id, start_date) "
                    "VALUES (:package_id, :start_date)"
                ),
                {"package_id": package_id, "start_date": first_date},
            )
            inserted += 1

        print(
            f"Seed de paquetes sintéticos: {inserted} insertados, "
            f"{skipped} ya existentes (se omiten)."
        )


if __name__ == "__main__":
    main()
