from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, Literal, Optional

from pydantic import BaseModel, Field, validator


class ProjectConfig(BaseModel):
    seed: int = 42
    timezone: str = "America/New_York"


class DataConfig(BaseModel):
    provider: Literal["yahoo", "local_csv"] = "yahoo"
    path: str = "data"
    equities_universe: str = "sp100.csv"
    start: date = Field(default_factory=lambda: date(2014, 1, 1))
    end: date = Field(default_factory=lambda: date(2025, 9, 1))


class CostConfig(BaseModel):
    spread_bps: float = 2.0
    impact_k: float = 0.9
    borrow_bps_month: float = 30.0

    @property
    def borrow_daily(self) -> float:
        return self.borrow_bps_month / 10000.0 / 21.0


class PortfolioConfig(BaseModel):
    target_vol_ann: float = 0.10
    max_name_weight: float = 0.02
    beta_neutral: bool = True
    sector_neutral: bool = True


class SleeveParams(BaseModel):
    lookback_mom_months: int | None = None
    skip_recent_month: bool | None = None
    qv_fields: list[str] | None = None
    top_quantile: float | None = None
    bottom_quantile: float | None = None
    z_entry: float | None = None
    exit: Literal["next_open", "next_close"] | None = None
    earnings_blackout_days: int | None = None
    min_dollar_vol: float | None = None


class SleeveConfig(BaseModel):
    enabled: bool = True
    rebalance: str | None = None
    risk_budget: float | None = None
    params: SleeveParams | None = None


class RegimeConfig(BaseModel):
    breadth_thresholds: Dict[str, float] = Field(default_factory=lambda: {"risk_off": 0.45, "risk_on": 0.6})
    corr_window_days: int = 60
    vix_curve_source: str = "csv"

    @validator("breadth_thresholds")
    def check_thresholds(cls, value: Dict[str, float]) -> Dict[str, float]:
        if not {"risk_off", "risk_on"}.issubset(value.keys()):
            raise ValueError("breadth_thresholds must include risk_off and risk_on")
        return value


class GovernanceConfig(BaseModel):
    dd_cut: float = 0.12
    loss_sigma_cut: float = 3.0


class ReportConfig(BaseModel):
    html: str = "reports/equities_bobe.html"
    trades_csv: str = "reports/trades.csv"


class LiveConfig(BaseModel):
    broker: Literal["alpaca", "dummy"] = "alpaca"
    poll_interval_sec: int = 60
    paper_start_cash: float = 100000.0


class SleevesConfig(BaseModel):
    A_tsmom: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=False))
    B_carry: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=False))
    C_xsec_qv: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=True, rebalance="M", risk_budget=0.85))
    D_intraday_rev: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=True, rebalance="D", risk_budget=0.15))
    E_vol_premia: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=False))

    def enabled_sleeves(self) -> Iterable[tuple[str, SleeveConfig]]:
        for name, cfg in self.model_dump().items():
            if isinstance(cfg, dict):
                enabled = cfg.get("enabled", False)
            else:
                enabled = getattr(cfg, "enabled", False)
            if enabled:
                yield name, getattr(self, name)


class Settings(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    costs: CostConfig = Field(default_factory=CostConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    sleeves: SleevesConfig = Field(default_factory=SleevesConfig)
    regimes: RegimeConfig = Field(default_factory=RegimeConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    reports: ReportConfig = Field(default_factory=ReportConfig)
    live: LiveConfig = Field(default_factory=LiveConfig)

    def enabled_sleeves(self) -> dict[str, SleeveConfig]:
        return {name: sleeve for name, sleeve in self.sleeves.enabled_sleeves()}
