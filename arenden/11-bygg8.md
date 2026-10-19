# 8 – Ringlistan görs för hand varje måndag
Etikett: bygg

Varje måndag morgon kör någon `python -m churn.score` på sin dator och mejlar filen till
kundtjänst. Blir hen sjuk blir det ingen ringlista.

**Uppgift:**
1. Lägg till ett jobb **ringlista** som laddar ner den godkända modellen, kör
   `python -m churn.score` och laddar upp `ringlista.csv` som artefakt. Det ska bara köras
   på main, aldrig på en pull request.
2. Låt hela pipelinen köras av sig själv varje måndag 06:00 svensk tid.
3. Lägg till en knapp för att köra pipelinen manuellt.

**Tänk på:** schemat anges med cron i UTC. Vad blir 06:00 svensk tid före och efter
omställningen till vintertid?

**Klart när:**
- [x] En manuell körning på main ger en artefakt med ringlistan.
- [x] Körningar på pull requests hoppar över ringlistan (grått jobb).

**Vad som gjordes**
- Nytt jobb `ringlista` i `ci.yml`. Det hämtar den godkända modellen från `utvardera`, kör `python -m churn.score` och laddar upp `ringlista-<sha>` som artefakt.
- Jobbet körs bara på `main` och hoppas över på pull requests.
- Schema: `0 4 * * 1` (måndagar 04:00 UTC).
- `workflow_dispatch` ger en knapp för manuell körning.
- `test` körs även vid schema och manuell körning, så att hela kedjan inte hoppas över när inga filer ändrats.

**Tidszon**
06:00 svensk tid är 04:00 UTC på sommartid och 05:00 UTC på vintertid. Jag valde 04:00 UTC så att listan alltid är klar senast 06:00: exakt 06:00 på sommaren och 05:00 på vintern. Hellre för tidigt än för sent för kundtjänst.
