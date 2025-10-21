from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ProjectConfig(BaseModel):
    seed: int = 42
    timezone: str = "America/New_York"


class DataConfig(BaseModel):
    provider: Literal["yahoo", "local_csv", "alpaca"] = "yahoo"
    path: str = "data"
    equities_universe: str = "sp100.csv"
    start: date = Field(default_factory=lambda: date(2014, 1, 1))
    end: Optional[date] = None
    timeframe: str = "1Day"
    symbols: Optional[list[str]] = None


class CostConfig(BaseModel):
    spread_bps: float = 2.0
    impact_k: float = 0.9
    borrow_bps_month: float = 30.0
    commission_bps: float = 0.5
    timing_slippage_bps: float = 1.0

    @property
    def borrow_daily(self) -> float:
        return self.borrow_bps_month / 10000.0 / 21.0


class PortfolioConfig(BaseModel):
    target_vol_ann: float = 0.10
    max_name_weight: float = 0.02
    beta_neutral: bool = True
    sector_neutral: bool = True


class SleeveParams(BaseModel):
    lookback_mom_months: Optional[int] = None
    skip_recent_month: Optional[bool] = None
    qv_fields: Optional[list[str]] = None
    top_quantile: Optional[float] = None
    bottom_quantile: Optional[float] = None
    z_entry: Optional[float] = None
    exit: Optional[Literal["next_open", "next_close"]] = None
    earnings_blackout_days: Optional[int] = None
    min_dollar_vol: Optional[float] = None


class SleeveConfig(BaseModel):
    enabled: bool = True
    rebalance: Optional[str] = None
    risk_budget: Optional[float] = None
    params: Optional[SleeveParams] = None


class RegimeConfig(BaseModel):
    breadth_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {"risk_off": 0.45, "risk_on": 0.6}
    )
    breadth_window_days: int = 200
    vol_window_days: int = 20
    corr_window_days: int = 60
    dispersion_window_days: int = 20
    vix_curve_source: str = "csv"

    @field_validator("breadth_thresholds")
    @classmethod
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
    runs_dir: str = "reports/runs"


class LiveConfig(BaseModel):
    broker: Literal["alpaca", "dummy"] = "alpaca"
    poll_interval_sec: int = 60
    paper_start_cash: float = 100000.0
    stop_loss_plpc: Optional[float] = None
    take_profit_plpc: Optional[float] = None
    news_enabled: bool = False
    news_symbols: int = 3
    news_company_headlines: int = 1
    news_general_headlines: int = 3
    news_refresh_minutes: int = 60
    news_lookback_hours: int = 24


class AlpacaConfig(BaseModel):
    data_base_url: str = "https://data.alpaca.markets"
    trading_base_url: str = "https://paper-api.alpaca.markets"
    key_env: str = "ALPACA_API_KEY_ID"
    secret_env: str = "ALPACA_API_SECRET_KEY"
    data_feed: Literal["iex", "sip"] = "iex"


class SleevesConfig(BaseModel):
    A_tsmom: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=False))
    B_carry: SleeveConfig = Field(default_factory=lambda: SleeveConfig(enabled=False))
    C_xsec_qv: SleeveConfig = Field(
        default_factory=lambda: SleeveConfig(
            enabled=True, rebalance="M", risk_budget=0.85
        )
    )
    D_intraday_rev: SleeveConfig = Field(
        default_factory=lambda: SleeveConfig(
            enabled=True, rebalance="D", risk_budget=0.15
        )
    )
    E_vol_premia: SleeveConfig = Field(
        default_factory=lambda: SleeveConfig(enabled=False)
    )

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
    alpaca: AlpacaConfig = Field(default_factory=AlpacaConfig)

    def enabled_sleeves(self) -> dict[str, SleeveConfig]:
        return {name: sleeve for name, sleeve in self.sleeves.enabled_sleeves()}
