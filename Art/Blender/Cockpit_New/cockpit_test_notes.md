# Lantern — eigenständiger Cockpit-Looktest

Neu entworfen und lokal mit Blender 5.2.2 LTS gebaut. Das vorhandene Cockpit-Modell, seine Bilder und sein Skript wurden für diesen Entwurf nicht als Vorlage verwendet. Alle Dateien dieser Variante liegen in `Art/Blender/Cockpit_New/`.

## Gestaltung

Kantige, breite Forschungsbrücke mit schräger dreiteiliger Panorama-Front, niedriger orangefarbener Kommandolehne und erhöhter Sternkarte. Links eine Forschungsstation mit Notizbuch und Tasse; rechts flacher Stauraum und ein verstauter Klappsitz. Zwei ruhige Lichtbänder ersetzen eine Folge von Spanten. Die ursprünglichen Farbtöne bleiben erhalten; die gelieferten Wasserfarbtexturen werden darüber multipliziert. Flache Schattierung, keine UV-Abwicklung.

## Geprüfte Daten

- **8.052 Dreiecke** nach Ersetzen der geometrischen Sternkartensymbole durch das Bild (ursprünglich 9.616) für die sieben Modulobjekte; zusätzlich 156 Dreiecke für 13 einfache Collider-Boxen.
- **4 × 8 × 3,5 m** Außenmaß, Front Blender **+Y**; alle sieben Objektursprünge am Bodenmittelpunkt **(0, 0, 0)**.
- Hintere Türöffnung **1,4 × 2,2 m**, ab Deckhöhe **Z = 0,12 m**. Deckplatten liegen bis Z = 0,132 m.
- Freiraum um den Stuhl: vorne ca. **1,31 m**, seitlich ca. **1,32 m**, zur hinteren seitlichen Einrichtung konservativ ca. **1,13 m**. Freie Höhe im Hauptgang mindestens **3,05 m**. Zusätzliche senkrechte Stichproben: **3,14 m**. Diese Geometrieprüfungen stammen vom ursprünglichen Looktest; die Wasserfarbänderung entfernt nur die alten Sternkartensymbole.
- Vier PNGs mit **1920 × 1080** Pixeln. Innenkamera bei **Z = 1,75 m**. Für die Draufsicht sind Dach und Lichtbänder entfernt und die Architektur bei Z = 1,48 m geschnitten; Möbel bleiben vollständig.
- FBX: **FBX All**, **−Z forward / Y up**, angewandte Transformationen; sieben Modulmeshes und 13 `COL_`-Boxen, keine Kameras, Lichter, Planet oder Schnittkopien.
- Ursprünglichen Export in einer frischen Blender-Szene wieder eingelesen: Objektzahl und Maße stimmen. Türdurchgang zusätzlich mit Strahlprüfungen kontrolliert. Details stehen in `cockpit_validation.json`.

## Grenzen und nächste Version

**Unity-Import und Begehung wurden nicht getestet.** In Unity die `COL_`-Meshes durch BoxCollider-Komponenten ersetzen und deren Renderer deaktivieren. Die Frontbarriere ist bewusst eine grobe Box vor dem nicht begehbaren Scheibenbereich. URP-Materialien, transparente Scheiben und Emissionsstärken müssen dort eingerichtet werden; das FBX überträgt den Blender-Look nicht vollständig. Die Tasse ist eine geschlossene Low-Poly-Form mit dunkler Oberseite.

Für eine zweite Version: Dach und Außenhaut als saubere zusammenhängende Geometrie ausarbeiten, Türsockel separat modularisieren, Anzeigen funktional animieren und die Einrichtung im Spiel mit dem Player-Controller erproben. Dieser Stand bleibt ein Looktest.

## Skript erneut ausführen

`cockpit_test.py` ist eine kommentierte Einzeldatei und auch im Texteditor der `.blend` abgelegt. In einer **neuen** Blender-Datei im Arbeitsbereich **Scripting** ausführen: Das Skript leert die aktuelle Szene. Zum Bauen ohne Bilder `RENDER = False` setzen. Standardziel ist dieser neue Ordner; ein erneuter Lauf überschreibt seine Ausgaben.

## Watercolour update

All six supplied images are packed into `cockpit_test.blend`. Surface materials use **Texture Coordinate (Object) → Mapping → Image Texture (Box, blend 0.2) → Mix/Multiply with the original base colour → Principled Base Color**. Hull, walls and floor use scale **0.5** (2 m repeat); console/frame metal uses **1** (1 m); orange seat cushions and the stowed jumpseat use **2** (0.5 m). Glass and illuminated buttons/light strips remain untextured.

The star-map image uses a separate **flat X/Z object-coordinate projection**, fitted once across the existing 1.54 × 0.58 m display, with **Extend** rather than Repeat, into Principled **Emission Color** (strength 2.5). It is fitted to the existing screen proportions. The old floating star/orbit glyphs were removed to keep the image unobstructed.

The original three cameras and lighting are preserved; `cockpit_closeup.png` adds a fourth camera at **Z = 1.75 m**. All four images are 1920 × 1080. `watercolour_validation.json` records the material assignments and checks.

**Reproduce the update:** run `apply_watercolour.py`. It reads `Backup_PlainColours/cockpit_test.blend`, applies the textures and renders all four views. Running `cockpit_test.py` alone builds the original plain-colour model. The plain-colour files are preserved in `Backup_PlainColours/`.

The updated FBX includes the revised screen geometry and material names. **Blender's box-projection/Multiply node graphs are not portable Unity materials**; reproduce the mapping in a URP triplanar shader for the same appearance in-game. This update was checked in Blender, not Unity.
