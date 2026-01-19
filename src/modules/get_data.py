from datetime import datetime
from pathlib import Path

import ee

SERVICE_ACCOUNT = "erkocadag@dataviz-484810.iam.gserviceaccount.com"
KEY_FILE = "service-account-key.json"
PROJECT = None
ERA5_COLLECTION = "ECMWF/ERA5_LAND/MONTHLY_AGGR"


def initialize(
    service_account: str = SERVICE_ACCOUNT,
    key_file: str | Path = KEY_FILE,
    project: str | None = PROJECT,
) -> None:
    key_path = Path(key_file).expanduser().resolve()
    if not key_path.exists():
        raise FileNotFoundError(f"Service-Account-Key nicht gefunden: {key_path}")

    credentials = ee.ServiceAccountCredentials(service_account, str(key_path))  # type: ignore[reportPrivateImportUsage]
    if project:
        ee.Initialize(credentials, project=project)
    else:
        ee.Initialize(credentials)


def test_connection() -> bool:
    initialize()
    ee.Number(1).getInfo()  # type: ignore[reportPrivateImportUsage]
    return True


def _add_one_month(dt: datetime) -> datetime:
    year = dt.year + (dt.month // 12)
    month = (dt.month % 12) + 1
    return datetime(year, month, 1)


def get_collection() -> ee.ImageCollection:  # type: ignore[reportPrivateImportUsage]
    initialize()
    return ee.ImageCollection(ERA5_COLLECTION)  # type: ignore[reportPrivateImportUsage]


def available_bands() -> list[str]:
    collection = get_collection()
    bands = collection.first().bandNames().getInfo()  # type: ignore[reportPrivateImportUsage]
    if bands is None:
        return []
    return list(bands)


def available_months() -> list[datetime]:
    collection = get_collection()
    stats = collection.reduceColumns(ee.Reducer.minMax(), ["system:time_start"]).getInfo()  # type: ignore[reportPrivateImportUsage]
    if not stats or stats.get("min") is None or stats.get("max") is None:
        return []
    start = datetime.utcfromtimestamp(stats["min"] / 1000)
    end = datetime.utcfromtimestamp(stats["max"] / 1000)

    months: list[datetime] = []
    cursor = datetime(start.year, start.month, 1)
    last = datetime(end.year, end.month, 1)
    while cursor <= last:
        months.append(cursor)
        cursor = _add_one_month(cursor)
    return months


def fetch_month_image(month: datetime, band: str) -> ee.Image:  # type: ignore[reportPrivateImportUsage]
    start = ee.Date(month.strftime("%Y-%m-01"))  # type: ignore[reportPrivateImportUsage]
    end = start.advance(1, "month")
    collection = get_collection().filterDate(start, end)
    return ee.Image(collection.select([band]).first())  # type: ignore[reportPrivateImportUsage]


if __name__ == "__main__":
    try:
        if test_connection():
            print("GEE-Verbindung erfolgreich.")
    except Exception as exc:  # noqa: BLE001
        print(f"GEE-Verbindung fehlgeschlagen: {exc}")
