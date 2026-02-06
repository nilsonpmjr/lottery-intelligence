from fastapi import APIRouter

from lottery_intelligence.core.config import CONFIG_LOTERIAS
from api.models import LotteryConfig, LotteriesResponse

router = APIRouter()


@router.get("/api/lotteries", response_model=LotteriesResponse)
def list_lotteries():
    configs = []
    for name, cfg in CONFIG_LOTERIAS.items():
        configs.append(
            LotteryConfig(
                name=name,
                preco=cfg["preco"],
                total_nums=cfg["total_nums"],
                escolhe=cfg["escolhe"],
                orcamento_alvo=cfg.get("orcamento_alvo", cfg["preco"] * 5),
            )
        )
    return LotteriesResponse(lotteries=configs)
