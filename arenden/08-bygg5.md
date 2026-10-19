# 5 – Bara testad kod till main
Etikett: bygg

Från och med nu ska ingen kunna lägga något på main som inte har passerat testerna och
utvärderingen.

**Uppgift:**
1. Låt workflowet köras på pull requests mot main.
2. Lägg in en regel för main (Settings → Branches eller Rules): pull request krävs, och
   testjobben och utvärderingsjobbet måste vara gröna innan merge.
3. Prova: gör en gren där modellen blir sämre (höj till exempel tröskeln med miljövariabeln
   `MIN_ROC_AUC`, eller ta bort en feature i en kopia). Öppna en pull request.

**Klart när:**
- [x] Pull requesten med den sämre modellen är röd och går inte att merga.
- [x] Du har länkat den här.


Pull request: https://github.com/LeoLindqvist123/mobil-fix/pull/11

1. **Workflowet körs på pull requests:** `on:` innehåller nu `push` och `pull_request`, båda mot `main`.
2. **Regel för main:** ett ruleset kräver en pull request innan merge, och att `test (3.11)`,
   `test (3.12)`, `test (3.13)` och `utvardera` är gröna. Bypass-listan är tom, så regeln gäller
   alla, även admins.
3. **Test:** i grenen `test/samre-modell` höjdes tröskeln till 0,95 med `MIN_ROC_AUC`. Modellen
   når bara 0,789, så `utvardera` blev rött och merge-knappen blev blockerad.