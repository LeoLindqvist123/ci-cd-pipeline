# Individuell VG-analys: MLOps-pipeline (Saldes Mobil AB)
**Författare:** Erfan Tahmasebi  
**Projekt:** CI/CD & MLOps Pipeline för churn-prediktion  
**Repo:** `LeoLindqvist123/ci-cd-pipeline`

---

## 1. Analys av teamets ursprungliga pipeline (Baseline)

### A. Robusthet (Hur fel och oväntade situationer hanteras)
* **Identifierad svaghet i baslinjen:**  
  I baslinjen förlitade sig datavalideringen enbart på statiska schemakontroller via Pandera (`validation/schema.py`). Den kontrollerade enbart strikta datatyper, null-värden och hårdkodade min/max-gränser (t.ex. `alder` mellan 18 och 100).  
  Pipelinen saknade skydd mot **Data Drift (kovariatskifte)** och volymtapp. Om en ny datafil levererades där alla rader tekniskt uppfyllde de statiska gränserna, men där datans statistiska egenskaper var kraftigt förändrade (t.ex. att medelkostnaden drivit iväg eller att datasetet tappat 90 % av raderna), släpptes den igenom utan varning. Modellen tränades därmed om på skev data.
* **Vald åtgärd:**  
  Implementerade en statistisk drift- och volymkontroll (`src/churn/drift.py`) som beräknar skift i standardavvikelser (Z-score) för numeriska kolumner samt fångar okända kategorier och volymtapp före modellträning.

### B. Driftsäkerhet (Säkerhet och stabilitet i produktionscontainern)
* **Identifierade svagheter i baslinjen:**  
  * **Root-behörighet:** Containern kördes ursprungligen som `root`, vilket bryter mot säkerhetsprincipen om minsta behörighet (Least Privilege).
  * **Saknad Healthcheck:** Dockerfile saknade en `HEALTHCHECK`-instruktion. Om FastAPI-processen eller modellen skulle hänga sig i produktion kunde en extern orkestrerare (t.ex. Kubernetes eller Docker Swarm) inte upptäcka felet och starta om containern.
  * **Onödig attackyta:** Baslinjens Docker-image innehöll verktyg som `/bin/uv` och temporära filer direkt i runtime-lagret.
* **Vald åtgärd:**  
  Införde en dedikerad icke-root-användare (`appuser`) samt lade till en inbyggd `HEALTHCHECK` mot `GET /health` som körs periodiskt.

### C. Resurshantering (Byggtider, lagringsutrymme och nätverk)
* **Identifierade svagheter i baslinjen:**  
  * **Single-stage build:** Docker-bygget var single-stage, vilket innebar att `/bin/uv` (~20 MB), temporära nedladdningscacher (`/root/.cache/uv` på ~75 MB) och onödig bytekod sparades i produktionslagret.
  * **Avsaknad av lager-cache:** GitHub Actions byggde om Docker-imagen från grunden vid varje commit utan att använda GitHub Actions cache-backend (`--cache-from type=gha`), vilket drog onödig CPU, nätverk och tid (16 sekunder per bygge).
  * **Onödiga testfiler:** Testfiler och `__pycache__` inuti `.venv` från tunga bibliotek tog upp diskutrymme i onödan.
* **Vald åtgärd:**  
  Skrev om `Dockerfile` till en **Multi-stage build** (`builder` -> `runtime`), rensade bytekod och testmappar i `.venv`, samt implementerade Docker Buildx med GitHub Actions lager-caching (`type=gha`).

### D. Förändrade datakällor (Mottagning av nya dataleveranser)
* **Identifierad svaghet i baslinjen:**  
  Pipelinen saknade en systematisk grind för att jämföra en ny leverans mot en godkänd referensbaslinje (`kundbas.csv`). Nya kategorier i `region` eller `abonnemang` som inte fanns i träningsdatan upptäcktes först vid modellinferens, vilket riskerade körtidsfel i produktion.
* **Vald åtgärd:**  
  Byggde en referensjämförelse som kontrollerar inkommande filer mot `kundbas.csv` och larmar omedelbart om nya, okända kategorier dyker upp.

---

## 2. Genomförda förbättringar (Mina två VG-Pull Requests)

### Förbättring 1: Multi-Stage Docker, Buildx Layer Cache & Healthcheck
* **Områden:** Resurshantering & Driftsäkerhet.
* **Tekniska ändringar:**
  1. `Dockerfile` delades upp i två steg (`builder` och `runtime`).
  2. Byggverktyget `uv` och wheel-cachen isolerades i byggstadiet och följer inte med till produktion.
  3. Rensning av `__pycache__` och testfiler i `.venv` med `find`-kommandon.
  4. Docker Buildx integrerat med `--cache-from type=gha` och `--cache-to type=gha,mode=max`.
  5. `HEALTHCHECK` mot `GET /health` var 15:e sekund.
  6. Körning som icke-root (`appuser`).

### Förbättring 2: Statistisk Data Drift-grind för säkra dataleveranser
* **Områden:** Robusthet & Förändrade datakällor.
* **Tekniska ändringar:**
  1. Skapade modulen `src/churn/drift.py` med funktionen `check_delivery_drift()`.
  2. **Volymkontroll:** Larmar om antalet rader i den nya leveransen sjunker med mer än 50 %.
  3. **Fördelningskontroll:** Beräknar skift i standardavvikelser för numeriska fält (Z-score) och fäller leveransen om skiftet överstiger 0.50 std.
  4. **Kategorikontroll:** Fångar okända kategorivärden i `region` och `abonnemang`.
  5. **Målvariabelkontroll:** Kontrollerar att andelen churn inte skiftar med mer än 15 procentenheter.
  6. Automatiserade tester i `tests/test_data.py` som verifierar att referensdata passerar medan skapad drift och volymfall stoppas deterministiskt.

---

## 3. Mätvärden: Före och efter

| Område / Mått | Före förbättring (Baseline, Körning #76) | Efter förbättring (VG-PR) | Förbättring & Värde |
| :--- | :--- | :--- | :--- |
| **Docker-byggtid** | **16 sekunder** | **11.3 sekunder** (kallt bygge) | **~30 % snabbare** byggtid vid första bygget |
| **Lager-caching (GHA)** | Ingen cache (alla lager byggs om) | `type=gha` sparat i GitHub Actions | Sparar CPU och nätverksresurser i Actions |
| **Container-säkerhet** | Kördes som `root`, saknade healthcheck | **`appuser`** (icke-root) + **`HEALTHCHECK`** | Högre driftsäkerhet, orkestrerare upptäcker låsningar |
| **Attackyta / Innehåll** | Innehöll `/bin/uv` (20 MB), temporära cacher | Endast minimal `.venv`, kod och modell | Mindre image, minimerad attackyta |
| **Data Drift-kontroll** | **0 kontroller** (passerade med 0 fel trots extrem drift) | **4 statistiska kontroller** (volym, Z-score, okända kategorier, target drift) | Förhindrar att modellen tränas om på skev data |
| **Körtid för driftgrind** | Fanns ej | **1.30 sekunder** (4 tester i `test_data.py`) | Fångar datadeformation omedelbart före träning |

---

## 4. Slutsats och MLOps-motivering

Genom dessa två förbättringar har pipelinen lyfts från en grundläggande CI-kedja till en produktionsnära MLOps-pipeline:
1. Pipelinen hushåller med resurser genom lager-caching och en slimmad container-image.
2. Driftsäkerheten stärks genom principen om minsta behörighet (`appuser`) och kontinuerliga hälsokontroller.
3. Modellen skyddas mot prestandatapp orsakade av tyst dataförändring genom att inkommande leveranser valideras både mot statiska schemaregler och statistisk drift.
