# Crew quarters — Sol / comparison build v2

Eigenständiger Entwurf nach `section-standard.md`, `mockup_quarters_v2.png` und dem Außenrumpf-Mockup. Gebaut und gerendert mit Blender 5.2.2 LTS. Alle Ausgaben und Arbeitsschritte dieser Variante liegen ausschließlich in `Quarters_Sol/`; die andere Vergleichsvariante wurde nicht gelesen oder verändert.

## Lieferumfang

- `quarters_Sol.blend` — gepackte Wasserfarbtexturen, editierbare benannte Teile, vier Kameras; Hauptkamera aktiv.
- `quarters_Sol.fbx` — Abschnitt, sieben Props und einfache Collider-Boxen; FBX All, −Z vorwärts, Y oben. Keine Kameras, Lichter oder Renderkulisse.
- `quarters_Sol.py` — kommentiertes, eigenständig ausführbares Bauskript, auch im Blender-Texteditor enthalten. **Leert die aktuelle Szene**; in einer neuen Datei ausführen. `RENDER = False` überspringt die Bilder.
- Vier PNGs mit 1920 × 1080: `quarters_Sol_mockup_view.png`, `quarters_Sol_topdown.png`, `quarters_Sol_exterior.png`, `quarters_Sol_closeup.png`.
- `validation_Sol.json` — Zahlen und Prüfungen.

## Dreiecke

| Teil | Dreiecke |
|---|---:|
| Gesamte Hülle / Einbauten einschließlich beider Türen | **7.392 / max. 8.000** |
| `Prop_Lockers_Sol` | 528 |
| `Prop_Dinette_Sol` | 484 |
| `Prop_Plant_Sol` | 388 |
| `Prop_Mug_Sol` | 288 |
| `Prop_Book_Sol` | 132 |
| `Prop_Jacket_Sol` | 104 |
| `Prop_Pictures_Sol` | 180 |
| **Gesamt ohne Collider und Renderkulisse** | **9.496 / max. 25.000** |

Alle Props bleiben unter 1.500 Dreiecken. Die 19 einfachen Collider-Boxen kommen mit weiteren 228 Dreiecken hinzu. Bolzengeometrie ist auf den Bullaugenring beschränkt; Flächenverschleiß und kleine Unregelmäßigkeiten kommen aus den Texturen.

## Standard und Aufbau

Außengrenzen X −2…2, Y −4…4, Z 0…3,5 m. Bodenoberfläche bei Z 0,2; flache Deckenunterseite bei Z 3,2. Obere Außenfasen 0,8 m, untere 0,5 m. Seiten und diagonale Wandstücke sind 0,25 m dick; Boden und Dach folgen ihren ausdrücklich vorgegebenen Höhen. Spanten an beiden Enden und im 2-m-Rhythmus. Ochre Rohrläufe gehen gerade bis zu den Endebenen: X/Z = (1,25 / 2,98) und (1,10 / 3,08) m.

Zwei zentrierte Türsockel, jeweils 1,4 × 2,2 m mit 0,25-m-Eckfasen. `Door_Front_Sol` und `Door_Back_Sol` sind separate, geschlossene Schiebetür-Panels. Die zusätzliche Suffix-Nennung erhält die geforderten Türnamen eindeutig für den Vergleich. Der Mittelweg ist mindestens 1 m breit; die engste Einrichtungskombination aus Leiter und Essecke lässt konservativ etwa 1,13 m frei. Geprüft wurde die durchgehende 1-m-Spur mit Strahlen bis über Kopfhöhe, bei als offen behandelten separaten Türpanels.

Alle Einbauten haben ihren Ursprung am Modul-Bodenmittelpunkt (0,0,0). Die sieben Props haben eigene Ursprünge in der Mitte ihrer unteren Begrenzung; für Wandprops bezieht sich das auf die gesamte hängende Form. Spinde beanspruchen ungefähr 1 × 1 m, die Essecke ungefähr 1 × 3 m. Die Frontausrichtung ist +Y.

Kamera-Augenhöhe **1,7 m über Deck**, also Welt-Z **1,9 m**. Für die Draufsicht sind Decke, obere Schrankteile und Kojenabdeckung entfernt; die übrige Architektur wird bei Z 1,65 geschnitten. Der Schnitt ist eine eigene reine Renderkopie; die exportierte Geometrie bleibt vollständig.

## Materialien und Prüfung

Alle fünf gelieferten Oberflächentexturen sind in der `.blend` gepackt. Object → Mapping → Image Texture (Box, Blend 0,2) → Multiply mit der Palettenfarbe → Principled Base Color. Rumpf/Wand/Boden skalieren mit 0,5; Metall mit 1; Stoff mit 2. Keine UV-Abwicklung. Glas und Lichtflächen bleiben untexturiert. Nur die Bullaugenkulisse mit Sternen und facettiertem Planeten ist in `RENDER_ONLY_Sol` abgelegt.

Geprüft: Außenmaß, flache Flächenschattierung, angewandte Skalierung, Einbauten-Ursprünge, Polygonbudgets, durchgehender Gang, beide Türöffnungen ohne Türpanels, Textur-Knotenketten und Bildgrößen. FBX in eine leere Blender-Szene zurückimportiert: 40 Meshes, einschließlich 19 Collidern, Maße 4 × 8 × 3,5 m; keine Renderobjekte.

## Abweichungen vom Bild und nächster Entwurf

- **Die zentrale hintere Tür bleibt sichtbar.** Deshalb stehen die zwei schmalen Spinde links und die Waschnische rechts davon. In der Hauptperspektive verdeckt die Koje einen Teil des äußeren Spinds. Das entspricht dem verbindlichen Tür- und Gangstandard, nicht exakt der vollflächigen Rückwand des Mockups.
- Die feste Länge von 8 m ergibt eine längere, stärker perspektivische Raumwirkung als das gemalte Bild. Farben und Wasserfarbwirkung sind aus den gelieferten Texturen aufgebaut; die gemalten Lichtflecken, Stofffalten und Materialkanten werden nicht pixelgenau nachgebildet.
- Pflanze, Jacke, Bettzeug und Bilder sind bewusst einfache facettierte Formen. Die Bilder sind geometrische Landschaftscollagen; der Planet ist eine stilisierte Renderkulisse.
- Der Außentest zeigt nur diesen einzelnen Modulrumpf mit Bullauge und Tür, ohne die Triebwerke, Flügel oder Anbauten des kompletten Schiffs im Außen-Mockup.

Als Nächstes würde ich die Kojenrahmen an ihren Ecken als durchgehende Meshes ausarbeiten, Jacke und Pflanze plastischer gestalten und Türanimation sowie Platzierung der Props mit dem Spielcontroller erproben. **Unity-Import, URP-Materialien und Begehung wurden nicht getestet.** Die Collider sind benannte Hilfsmeshes; in Unity daraus BoxCollider-Komponenten erstellen. Die Blender-Box-Projektionsknoten werden nicht als fertiger URP-Triplanar-Shader über FBX übertragen.
