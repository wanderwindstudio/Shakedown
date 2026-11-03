using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace TestPlanet
{
    public sealed class PlanetHud : MonoBehaviour
    {
        [SerializeField, Tooltip("Unity's bundled font converted to a TextMeshPro SDF font asset.")]
        TMP_FontAsset font;
        [SerializeField, Tooltip("Primary HUD text colour.")]
        Color textColour = new Color(.87f, .93f, .88f);
        [SerializeField, Tooltip("Warning text colour.")]
        Color warningColour = new Color(1, .66f, .32f);
        [SerializeField, Tooltip("Main readout text size at 1080p.")]
        float readoutSize = 26;
        [SerializeField, Tooltip("Warning title text size at 1080p.")]
        float warningSize = 46;
        [SerializeField, Tooltip("HUD margin from screen edges at 1080p.")]
        float margin = 48;
        [SerializeField, Tooltip("Reticle size in screen pixels.")]
        float reticleSize = 3;
        [SerializeField, Tooltip("Seconds between text refreshes; avoids needless per-frame text allocations.")]
        float refreshInterval = .1f;
        float nextRefresh;
        PlanetTide tide;
        PlanetPlayer player;
        TextMeshProUGUI countdown, warning, altitude;
        Image fade;
        Canvas canvas;
        public float Fade
        {
            set
            {
                if (fade != null)
                    fade.color = new Color(0, 0, 0, value);
            }
        }

        public void Initialize(PlanetTide tideSystem, PlanetPlayer explorer)
        {
            tide = tideSystem;
            player = explorer;
            var root = new GameObject("Survey HUD · TextMeshPro", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
            root.transform.SetParent(transform, false);
            canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceCamera;
            canvas.worldCamera = player.Eyes;
            canvas.planeDistance = .5f;
            canvas.sortingOrder = 100;
            var scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = .5f;
            Text("PELAGIC   /   SURVEY 01", new Vector2(margin, -margin), new Vector2(700, 45), new Vector2(0, 1), readoutSize, TextAlignmentOptions.TopLeft);
            countdown = Text("", new Vector2(-margin, -margin), new Vector2(600, 45), new Vector2(1, 1), readoutSize, TextAlignmentOptions.TopRight);
            altitude = Text("", new Vector2(-margin, margin), new Vector2(620, 40), new Vector2(1, 0), 20, TextAlignmentOptions.BottomRight);
            Text("WASD  move    SHIFT  sprint    SPACE  jump    ESC  cursor", new Vector2(margin, margin), new Vector2(1000, 40), new Vector2(0, 0), 18, TextAlignmentOptions.BottomLeft);
            warning = Text("", new Vector2(0, 140), new Vector2(1200, 150), new Vector2(.5f, .5f), warningSize, TextAlignmentOptions.Center);
            warning.color = warningColour;
            var dot = new GameObject("Small reticle", typeof(RectTransform), typeof(Image));
            dot.transform.SetParent(root.transform, false);
            var rect = dot.GetComponent<RectTransform>();
            rect.anchorMin = rect.anchorMax = new Vector2(.5f, .5f);
            rect.sizeDelta = Vector2.one * reticleSize;
            dot.GetComponent<Image>().color = new Color(textColour.r, textColour.g, textColour.b, .55f);
            var fader = new GameObject("Respawn fade", typeof(RectTransform), typeof(Image));
            fader.transform.SetParent(root.transform, false);
            rect = fader.GetComponent<RectTransform>();
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            fade = fader.GetComponent<Image>();
            fade.color = Color.clear;
            fade.raycastTarget = false;
        }

        TextMeshProUGUI Text(string content, Vector2 position, Vector2 size, Vector2 anchor, float fontSize, TextAlignmentOptions alignment)
        {
            var go = new GameObject("HUD text", typeof(RectTransform));
            go.SetActive(false);
            go.transform.SetParent(canvas.transform, false);
            var rect = go.GetComponent<RectTransform>();
            rect.anchorMin = rect.anchorMax = anchor;
            rect.pivot = anchor;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            var text = go.AddComponent<TextMeshProUGUI>();
            text.font = font;
            text.fontSize = fontSize;
            text.color = textColour;
            text.alignment = alignment;
            text.text = content;
            text.raycastTarget = false;
            go.SetActive(true);
            return text;
        }

        public void SetReviewCamera(Camera camera)
        {
            if (canvas != null)
                canvas.worldCamera = camera;
        }

        void Update()
        {
            if (tide == null || Time.unscaledTime < nextRefresh)
                return;
            nextRefresh = Time.unscaledTime + refreshInterval;
            int seconds = Mathf.CeilToInt(tide.Countdown);
            countdown.text = $"Next wave: {seconds / 60}:{seconds % 60:00}";
            bool safe = player.Position.y > tide.Crest + 2;
            altitude.text = $"ALT  {player.Position.y:000} m     /     " + (safe ? "ABOVE CREST · SAFE" : "CLIMB TO HIGH GROUND");
            warning.text = tide.Phase == PlanetTide.TidePhase.Drawdown ? "WAVE INCOMING\n<size=22>Sea retreat detected. Reach the crater rim.</size>" : tide.Phase == PlanetTide.TidePhase.Wave ? "SURGE PASSING\n<size=22>Stay above 60 metres.</size>" : "";
        }
    }
}
