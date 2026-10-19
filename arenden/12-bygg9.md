# 9 – Samma installationssteg står på fyra ställen
Etikett: bygg

Varje jobb har nu samma tre steg: checkout, installera Python, installera paketen. Ändrar vi
Python-version eller cache måste vi ändra på fyra ställen.

**Uppgift:** bryt ut installationen till en egen återanvändbar del, en *composite action* i
`.github/actions/` eller ett återanvändbart workflow. Motivera valet här.

**Klart när:**
- [x] Installationen beskrivs på ett ställe och används av alla jobb.
- [x] Pipelinen är fortfarande grön.

**Vad som gjordes**
- Ny composite action `.github/actions/installera/action.yml` som installerar Python (med pip-cache) och projektets paket.
- Inputs: `python-version` (standard `3.11`) och `paket` (standard `.`). `test` skickar med sin matris-version och `.[dev]`.
- Alla fyra jobben (`test`, `train`, `utvardera`, `ringlista`) använder nu actionen.
- `.github/actions/**` tillagd i paths-filter, så att ändringar i actionen också triggar testerna.

**Varför composite action och inte återanvändbart workflow**
Det som upprepades var några steg inuti jobben, inte hela jobb. En composite action är just en samling steg som kan användas inuti ett jobb. Ett återanvändbart workflow ersätter hela jobb och passar bättre när flera repon ska dela en hel pipeline. Här hade det krävt att varje jobb byggdes om.

checkout ligger kvar i varje jobb, eftersom actionen finns i repot och repot måste vara utcheckat innan den kan användas.
