from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class LotteryName(str, Enum):
    megasena = "megasena"
    lotofacil = "lotofacil"
    lotomania = "lotomania"
    diadesorte = "diadesorte"


class GenerationJobRequest(BaseModel):
    loteria: LotteryName
    orcamento: float = Field(gt=0, le=500)
    run_backtest: bool = True
    backtest_last_n: int = Field(default=0, ge=0)


class GameResult(BaseModel):
    numbers: List[int]
    source: str
    tag: str


class GenerationStats(BaseModel):
    total_games: int
    v3_count: int
    v5_count: int


class PerGameStat(BaseModel):
    game_index: int
    avg_hits: float
    max_hits: int
    min_hits: int


class BacktestResult(BaseModel):
    global_avg: float
    global_max: int
    per_game_stats: List[PerGameStat]
    tested_draws: int


class GenerationJobResponse(BaseModel):
    job_id: str
    loteria: LotteryName
    orcamento: float
    games: List[GameResult]
    stats: GenerationStats
    backtest: Optional[BacktestResult] = None
    error: Optional[str] = None


class LotteryConfig(BaseModel):
    name: str
    preco: float
    total_nums: int
    escolhe: int
    orcamento_alvo: float


class LotteriesResponse(BaseModel):
    lotteries: List[LotteryConfig]


class HealthResponse(BaseModel):
    status: str
    db_exists: bool
    db_tables: List[str]
