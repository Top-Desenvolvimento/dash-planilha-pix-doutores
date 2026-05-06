from __future__ import annotations

import os
import subprocess
from datetime import date


ANO = 2026


def rodar(comando: list[str], env_extra: dict[str, str] | None = None) -> None:
    env = os.environ.copy()

    if env_extra:
        env.update(env_extra)

    print(f"[RUN] {' '.join(comando)}")
    subprocess.run(comando, check=True, env=env)


def meses_anteriores_ao_atual() -> list[str]:
    hoje = date.today()

    if hoje.year == ANO:
        mes_final = hoje.month - 1
    else:
        mes_final = 12

    if mes_final < 1:
        return []

    return [f"{ANO}-{mes:02d}" for mes in range(1, mes_final + 1)]


def main() -> None:
    meses = meses_anteriores_ao_atual()

    if not meses:
        print("[INFO] Nenhum mês anterior para recarregar.")
        return

    print(f"[INFO] Meses anteriores que serão recarregados: {', '.join(meses)}")

    for competencia in meses:
        print(f"\n[INFO] Recarregando competência: {competencia}")
        rodar(
            ["python", "coletor_pix.py"],
            {
                "COMPETENCIA": competencia,
                "MODO_COLETA": "rapido",
            },
        )

    print("\n[INFO] Regenerando dashboard")
    rodar(["python", "generate_data.py"])
    rodar(["python", "generate_dashboard.py"])

    print("[OK] Histórico de meses anteriores recarregado com sucesso.")


if __name__ == "__main__":
    main()
