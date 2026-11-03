using System;
using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public interface IShipCommand { void Execute(); void Undo(); }

    public sealed class CellCommand : IShipCommand
    {
        readonly ShipGrid grid;
        readonly Vector3Int position;
        readonly ShipCell? before, after;
        readonly Action<Vector3Int> changed;
        public CellCommand(ShipGrid grid, Vector3Int position, ShipCell? after, Action<Vector3Int> changed)
        {
            this.grid = grid; this.position = position; this.after = after; this.changed = changed;
            before = grid.TryGet(position, out var cell) ? cell : (ShipCell?)null;
        }
        void Apply(ShipCell? value)
        {
            if (value.HasValue) grid.Set(position, value.Value); else grid.Remove(position);
            changed(position);
        }
        public void Execute() => Apply(after);
        public void Undo() => Apply(before);
    }

    public sealed class ShipHistory
    {
        const int Capacity = 256;
        readonly List<IShipCommand> commands = new List<IShipCommand>();
        int cursor;
        public void Execute(IShipCommand command)
        {
            commands.RemoveRange(cursor, commands.Count - cursor);
            command.Execute();
            commands.Add(command);
            if (commands.Count > Capacity) commands.RemoveAt(0);
            cursor = commands.Count;
        }
        public bool Undo() { if (cursor == 0) return false; commands[--cursor].Undo(); return true; }
        public bool Redo() { if (cursor == commands.Count) return false; commands[cursor++].Execute(); return true; }
        public void Clear() { commands.Clear(); cursor = 0; }
    }
}
