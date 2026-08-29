from datetime import datetime

import yaml
from pydantic import BaseModel

from app.core.contracts import FeeSchedule


class Constant(BaseModel):
    name: str
    value: float
    scope: str
    derivation_method: str = "manual_default"
    derived_from: str
    valid_range: list[float] | None = None
    gates: str
    unit: str | None = None


class Registry:
    def __init__(self, path=None):
        if path is None:
            from app.config import BASE_DIR
            path = BASE_DIR / "constants_v0.yaml"
        raw = yaml.safe_load(open(path))
        self.version = raw["version"]
        self.loaded_at = datetime.now()
        self._c = {c["name"]: Constant(**c) for c in raw["constants"]}
        self.fee_schedules = {fs["schedule_id"]: FeeSchedule(**fs)
                              for fs in raw.get("fee_schedules", [])}
        for c in self._c.values():
            if c.valid_range and not c.valid_range[0] <= c.value <= c.valid_range[1]:
                raise ValueError(f"{c.name}={c.value} outside {c.valid_range}")
        for scope in ("mapping", "match", "exception"):
            ws = [c.value for c in self._c.values() if c.name.startswith(f"w_{scope}_")]
            if ws and abs(sum(ws) - 1.0) > 1e-6:
                raise ValueError(f"{scope} weights sum to {sum(ws)}")

    def __getitem__(self, k):
        return self._c[k].value


REG = Registry()
