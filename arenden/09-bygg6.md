# 6 – En README-ändring startar träning
Etikett: bygg

Igår rättade någon ett stavfel i README:n. Det startade hela pipelinen, med träning och allt.

**Uppgift:** begränsa när workflowet startar, så att bara ändringar i kod, data, tester,
beroenden eller workflowet självt startar det.

**Tänk på:** om ett jobb är ett krav för merge (ärende 5) och workflowet inte startar alls,
vad händer då med en pull request som bara ändrar README:n? Skriv vad du ser.

**Klart när:**
- [x] En commit som bara ändrar README:n startar ingen körning.
- [x] En commit i `src/` gör det.

**Vad jag ser:** En pull request som bara ändrar README:n startar ingen körning, eftersom
`paths`-filtret hoppar över den. Men regeln från ärende 5 kräver att `test (3.11)`,
`test (3.12)`, `test (3.13)` och `utvardera` är gröna. De körs aldrig, så de står kvar som
"Expected — Waiting for status to be reported", och pull requesten går inte att merga.

**Lösning:** Workflowet startar nu alltid. Jobbet `andringar` kollar vilka filer som ändrats,
och test, träning och utvärdering körs bara om kod, data, tester, beroenden eller workflowet
ändrats. Jobbet `ci-klar` körs alltid och blir grönt om inget misslyckades. Regeln för main
kräver bara `ci-klar`.
