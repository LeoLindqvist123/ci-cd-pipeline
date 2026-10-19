# 7 – Tre pushar i rad ger tre körningar
Etikett: bygg

När man pushar tre gånger på en minut körs tre hela pipelines, fast bara den sista spelar roll.

**Uppgift:** se till att en ny push avbryter körningen som redan pågår på samma gren, men
aldrig körningar på andra grenar.

**Klart när:**
- [x] Två snabba pushar i rad ger en avbruten och en färdig körning i Actions.

Jag lade till `concurrency` i `ci.yml`:

    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true

Gruppen byggs av workflowets namn och grenen (eller pull requesten). Två pushar till samma
gren hamnar i samma grupp, och då avbryts den pågående körningen. Pushar till andra grenar
får en egen grupp och påverkas inte.

Test: i pull request #18 startade körning #38 när den öppnades. En tom commit direkt efter
startade #39, och då avbröts #38 (Cancelled) medan #39 körde klart.