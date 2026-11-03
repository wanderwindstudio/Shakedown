using System.IO;
using UnityEditor;

namespace TestPlanet.Editor
{
    [InitializeOnLoad]
    public static class PlanetCommands
    {
        static double nextPoll;
        static PlanetCommands()
        {
            EditorApplication.update += Poll;
        }

        static void Poll()
        {
            if (EditorApplication.timeSinceStartup < nextPoll)
                return;
            nextPoll = EditorApplication.timeSinceStartup + 1;
            // Local review automation only. No command is ever shipped in the game.
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                return;
            const string path = "/tmp/planet-review-command";
            if (!File.Exists(path))
                return;
            string command = File.ReadAllText(path).Trim();
            File.Delete(path);
            if (command == "quit")
            {
                EditorApplication.Exit(0);
                return;
            }

            if (command == "refresh")
            {
                AssetDatabase.Refresh();
                return;
            }

            if (int.TryParse(command, out int stage))
                PlanetBuild.Advance(stage);
        }
    }
}
