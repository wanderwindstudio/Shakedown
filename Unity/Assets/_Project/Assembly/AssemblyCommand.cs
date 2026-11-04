using System;
using Shakedown.Ship;

namespace Shakedown.Assembly
{
    public sealed class AssemblyCommand : IShipCommand
    {
        readonly AssemblyData before, after;
        readonly Action<AssemblyData> apply;
        public AssemblyCommand(AssemblyData before, AssemblyData after, Action<AssemblyData> apply)
        {
            this.before = before.Copy();
            this.after = after.Copy();
            this.apply = apply;
        }
        public void Execute() => apply(after.Copy());
        public void Undo() => apply(before.Copy());
    }
}
