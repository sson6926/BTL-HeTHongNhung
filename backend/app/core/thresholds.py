"""
Ngưỡng mặc định cho từng loại ao.
Khi tạo device mới, backend tự seed các threshold này vào DB.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DefaultThreshold:
    metric_type: str
    min_value: Optional[float]
    max_value: Optional[float]
    unit: Optional[str]
    action_target: Optional[str]
    action_command: Optional[str]
    auto_action: bool = False


# ---------------------------------------------------------------------------
# Ngưỡng theo từng loại ao
# ---------------------------------------------------------------------------

_CA_TRA = [
    DefaultThreshold("o2",          3.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.5,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 15.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          6.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 32.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 1500, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 50.0, "NTU",  None,         None),
]

_CA_RO_PHI = [
    DefaultThreshold("o2",          4.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.5,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 20.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          6.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 35.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 1000, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 40.0, "NTU",  None,         None),
]

_CA_CHEP = [
    DefaultThreshold("o2",          4.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.6,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 15.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          6.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 30.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 1000, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 50.0, "NTU",  None,         None),
]

_TOM_THE = [
    DefaultThreshold("o2",          5.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.3,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 25.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          7.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 30.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 2000, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 30.0, "NTU",  None,         None),
]

_TOM_SU = [
    DefaultThreshold("o2",          5.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.3,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 30.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          7.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 30.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 3000, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 25.0, "NTU",  None,         None),
]

# Generic – dùng khi không chỉ định pond_type
_GENERIC = [
    DefaultThreshold("o2",          5.0,  None, "mg/L", "oxygen",     "ON"),
    DefaultThreshold("nh3",         None, 0.5,  "mg/L", "pump_drain", "CHANGE_WATER"),
    DefaultThreshold("water_level", 20.0, None, "cm",   "pump_fill",  "ON"),
    DefaultThreshold("ph",          6.5,  8.5,  None,   None,         None),
    DefaultThreshold("temperature", None, 35.0, "°C",   None,         None),
    DefaultThreshold("tds",         None, 1000, "ppm",  None,         None),
    DefaultThreshold("turbidity",   None, 30.0, "NTU",  None,         None),
]

# ---------------------------------------------------------------------------
# Map pond_type → danh sách ngưỡng mặc định
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS: dict[str, list[DefaultThreshold]] = {
    "ca_tra":    _CA_TRA,
    "ca_ro_phi": _CA_RO_PHI,
    "ca_chep":   _CA_CHEP,
    "tom_the":   _TOM_THE,
    "tom_su":    _TOM_SU,
    "generic":   _GENERIC,
}

POND_TYPE_LABELS: dict[str, str] = {
    "ca_tra":    "Ao cá tra / basa",
    "ca_ro_phi": "Ao cá rô phi",
    "ca_chep":   "Ao cá chép",
    "tom_the":   "Ao tôm thẻ chân trắng",
    "tom_su":    "Ao tôm sú",
    "generic":   "Chung (không xác định)",
}
