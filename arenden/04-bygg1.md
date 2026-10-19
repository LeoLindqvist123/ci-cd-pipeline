# 1 – CI tar för lång tid
Etikett: bygg

Varje push installerar pandas och scikit-learn från noll. Själva träningen tar bara ett par
sekunder, så nästan hela körtiden är paketinstallation. Utvecklarna sitter och väntar.

**Uppgift:** återanvänd nedladdade paket mellan körningar.

**Tips:** `actions/setup-python` har inbyggd cache för pip. Vad ska cachenyckeln bygga på,
så att cachen byts ut när beroendena ändras men inte annars?

**Klart när:**
- [x] Andra körningen efter ändringen visar att cachen återställdes (sök efter `cache` i loggen).
- [x] Du har antecknat körtiden före och efter här (används i A1).

## Svar

Cachenyckel: Bygger på `pyproject.toml`. Ändras beroendena får cachen en ny nyckel, annars
återanvänds den.

Cachen återställdes: `Cache restored from key: setup-python-Linux-x64-24.04-Ubuntu-python-3.13.15-pip-ef3da5c2...`

Före: ca 30 s totalt, pip install 25 s
Efter: 30 s totalt, pip install  s

Slutsats: Cachen fungerar, men CI blev inte snabbare. Cachen sparar bara nedladdningen av
paketen. Installationen görs ändå varje gång, och det är den som tar tid.
