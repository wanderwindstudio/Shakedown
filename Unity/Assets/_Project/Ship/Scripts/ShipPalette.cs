using UnityEngine;
namespace Shakedown.Ship
{
    public static class ShipPalette
    {
        public static readonly string[] Names = { "Hull grey", "Lavender", "Slate blue", "Sea green", "Sage", "Ochre", "Clay", "Charcoal" };
        public static readonly Color[] Colours = {
            new Color(.55f,.56f,.61f), new Color(.58f,.49f,.64f), new Color(.37f,.48f,.61f), new Color(.32f,.53f,.53f),
            new Color(.51f,.59f,.48f), new Color(.67f,.56f,.37f), new Color(.65f,.43f,.39f), new Color(.29f,.29f,.35f) };
        public static Color Get(int index) => Colours[Mathf.Clamp(index, 0, 7)];
    }
}
