from pydantic import BaseModel


class Metric(BaseModel):
    label: str
    value: str


class AirQualityMetric(BaseModel):
    label: str
    status: str
    value: str
    tone: str


class InfoRow(BaseModel):
    label: str
    value: str
    meta: str | None = None


class ProductPricePoint(BaseModel):
    date: str
    price: int


class ProductStorePrice(BaseModel):
    name: str
    price: int
    location: str


class ProductPriceInfo(BaseModel):
    name: str
    category: str
    current_price: int
    previous_price: int
    unit: str
    change: float
    trend: str
    stores: list[ProductStorePrice]
    graph: list[ProductPricePoint]


class NoticeInfo(BaseModel):
    title: str
    description: str


class NearbyFacilityInfo(BaseModel):
    name: str
    category: str
    address: str
    description: str
    source_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class LifeInfoResponse(BaseModel):
    district: str
    generated_at: str
    weather_summary: str
    temperature: str
    feels_like: str
    condition: str
    weather_metrics: list[Metric]
    air_quality: list[AirQualityMetric]
    weekly_forecast: list[list[str]]
    roads: list[InfoRow]
    transit: list[InfoRow]
    economy: list[InfoRow]
    safety_alerts: list[NoticeInfo]
    product_prices: list[ProductPriceInfo]
    notices: list[NoticeInfo]
    nearby_facilities: list[NearbyFacilityInfo]
