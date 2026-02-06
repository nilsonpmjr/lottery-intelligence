import os
import uuid

from fastapi import APIRouter, HTTPException

from api.models import (
    BacktestResult,
    GameResult,
    GenerationJobRequest,
    GenerationJobResponse,
    GenerationStats,
    PerGameStat,
)
from lottery_intelligence.core.hybrid import gerar_jogos_hybrid
from lottery_intelligence.intelligence.backtest import run_backtest

router = APIRouter()

DB_PATH = "loterias.db"


@router.post("/api/generation-jobs", response_model=GenerationJobResponse)
def create_generation_job(req: GenerationJobRequest):
    if not os.path.isfile(DB_PATH):
        raise HTTPException(status_code=503, detail="Database not available")

    job_id = str(uuid.uuid4())
    loteria = req.loteria.value

    games_with_meta, stats_info = gerar_jogos_hybrid(loteria, req.orcamento)

    games = [
        GameResult(
            numbers=g["numbers"],
            source=g["source"],
            tag=g["tag"],
        )
        for g in games_with_meta
    ]

    stats = GenerationStats(
        total_games=stats_info.get("total_games", 0),
        v3_count=stats_info.get("v3_count", 0),
        v5_count=stats_info.get("v5_count", 0),
    )

    backtest_result = None
    if req.run_backtest:
        try:
            games_only = [g["numbers"] for g in games_with_meta]
            bt = run_backtest(games_only, loteria, last_n=req.backtest_last_n)
            if "error" not in bt:
                backtest_result = BacktestResult(
                    global_avg=bt["global_avg"],
                    global_max=bt["global_max"],
                    per_game_stats=[
                        PerGameStat(**pgs) for pgs in bt["per_game_stats"]
                    ],
                    tested_draws=bt["tested_draws"],
                )
        except Exception:
            pass

    return GenerationJobResponse(
        job_id=job_id,
        loteria=req.loteria,
        orcamento=req.orcamento,
        games=games,
        stats=stats,
        backtest=backtest_result,
    )
