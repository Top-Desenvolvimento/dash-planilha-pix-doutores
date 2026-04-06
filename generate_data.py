name: Coleta PIX Doutores

on:
  workflow_dispatch:
    inputs:
      modo_coleta:
        description: "Modo de coleta: rapido ou historico"
        required: false
        default: "rapido"
  schedule:
    - cron: "*/5 * * * *"

permissions:
  contents: write

jobs:
  coletar:
    runs-on: ubuntu-22.04

    steps:
      - name: Checkout do código
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar dependências
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          python -m playwright install chromium

      - name: Definir modo
        id: modo
        run: |
          if [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "modo=${{ github.event.inputs.modo_coleta }}" >> $GITHUB_OUTPUT
          else
            echo "modo=rapido" >> $GITHUB_OUTPUT
          fi

      - name: Rodar coleta
        env:
          MODO_COLETA: ${{ steps.modo.outputs.modo }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
        run: |
          python coletor_pix.py
          python generate_data.py

      - name: Commit dos arquivos
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --cached --quiet || git commit -m "Atualiza dashboard PIX Doutores"
          git push
