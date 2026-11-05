# Lantern — eigenständiger Cockpit-Looktest

Neu entworfen und lokal mit Blender 5.2.2 LTS gebaut. Das vorhandene Cockpit-Modell, seine Bilder und sein Skript wurden für diesen Entwurf nicht als Vorlage verwendet. Alle Dateien dieser Variante liegen in `Art/Blender/Cockpit_New/`.

## Gestaltung

Kantige, breite Forschungsbrücke mit schräger dreiteiliger Panorama-Front, niedriger orangefarbener Kommandolehne und erhöhter Sternkarte. Links eine Forschungsstation mit Notizbuch und Tasse; rechts flacher Stauraum und ein verstauter Klappsitz. Zwei ruhige Lichtbänder ersetzen eine Folge von Spanten. Schlichte Farbmaterialien, flache Schattierung, keine Texturen oder UV-Abwicklung.

## Geprüfte Daten

- **9.616 Dreiecke** für die sieben Modulobjekte; zusätzlich 156 Dreiecke für 13 einfache Collider-Boxen.
- **4 × 8 × 3,5 m** Außenmaß, Front Blender **+Y**; alle sieben Objektursprünge am Bodenmittelpunkt **(0, 0, 0)**.
- Hintere Türöffnung **1,4 × 2,2 m**, ab Deckhöhe **Z = 0,12 m**. Deckplatten liegen bis Z = 0,132 m.
- Freiraum um den Stuhl: vorne ca. **1,31 m**, seitlich ca. **1,32 m**, zur hinteren seitlichen Einrichtung konservativ ca. **1,13 m**. Freie Höhe im Hauptgang mindestens **3,05 m**. Zusätzliche senkrechte Stichproben: **3,14 m**.
- Drei PNGs mit **1920 × 1080** Pixeln. Innenkamera bei **Z = 1,75 m**. Für die Draufsicht sind Dach und Lichtbänder entfernt und die Architektur bei Z = 1,48 m geschnitten; Möbel bleiben vollständig.
- FBX: **FBX All**, **−Z forward / Y up**, angewandte Transformationen; sieben Modulmeshes und 13 `COL_`-Boxen, keine Kameras, Lichter, Planet oder Schnittkopien.
- Export in einer frischen Blender-Szene wieder eingelesen: Objektzahl und Maße stimmen. Türdurchgang zusätzlich mit Strahlprüfungen kontrolliert. Details stehen in `cockpit_validation.json`.

## Grenzen und nächste Version

**Unity-Import und Begehung wurden nicht getestet.** In Unity die `COL_`-Meshes durch BoxCollider-Komponenten ersetzen und deren Renderer deaktivieren. Die Frontbarriere ist bewusst eine grobe Box vor dem nicht begehbaren Scheibenbereich. URP-Materialien, transparente Scheiben und Emissionsstärken müssen dort eingerichtet werden; das FBX überträgt den Blender-Look nicht vollständig. Die Tasse ist eine geschlossene Low-Poly-Form mit dunkler Oberseite.

Für eine zweite Version: Dach und Außenhaut als saubere zusammenhängende Geometrie ausarbeiten, Türsockel separat modularisieren, Anzeigen funktional animieren und die Einrichtung im Spiel mit dem Player-Controller erproben. Dieser Stand bleibt ein Looktest.

## Skript erneut ausführen

`cockpit_test.py` ist eine kommentierte Einzeldatei und auch im Texteditor der `.blend` abgelegt. In einer **neuen** Blender-Datei im Arbeitsbereich **Scripting** ausführen: Das Skript leert die aktuelle Szene. Zum Bauen ohne Bilder `RENDER = False` setzen. Standardziel ist dieser neue Ordner; ein erneuter Lauf überschreibt seine Ausgaben.
