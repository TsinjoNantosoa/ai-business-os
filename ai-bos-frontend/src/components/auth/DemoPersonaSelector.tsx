import { BarChart3, Briefcase, Building2, Users } from 'lucide-react';

const PERSONAS = [
  { email: 'ceo@demo.aibos.io', label: 'CEO', detail: 'Vue exécutive', icon: Building2 },
  { email: 'sales@demo.aibos.io', label: 'Sales', detail: 'CRM & pipeline', icon: Briefcase },
  { email: 'finance@demo.aibos.io', label: 'Finance', detail: 'Cash & factures', icon: BarChart3 },
  { email: 'hr@demo.aibos.io', label: 'RH', detail: 'Équipe & congés', icon: Users },
] as const;

export function DemoPersonaSelector({ onSelect, loading }: { onSelect: (email: string) => void; loading?: boolean }) {
  return (
    <section className="rounded-lg border border-primary/25 bg-primary/[.045] p-4" aria-labelledby="demo-personas-title">
      <div className="mb-3">
        <h2 id="demo-personas-title" className="text-sm font-semibold">Explorer AI BOS</h2>
        <p className="mt-1 text-xs text-muted-foreground">Choisissez une perspective métier. L’accès sécurisé est lancé automatiquement.</p>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {PERSONAS.map((persona) => {
          const Icon = persona.icon;
          return (
            <button key={persona.email} type="button" disabled={loading} onClick={() => onSelect(persona.email)} className="group rounded-md border border-border bg-card p-3 text-left transition-[border-color,background-color] hover:border-primary/40 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:opacity-50">
              <Icon className="h-4 w-4 text-primary" aria-hidden />
              <span className="mt-2 block text-xs font-semibold">{persona.label}</span>
              <span className="mt-0.5 block text-[11px] text-muted-foreground">{persona.detail}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
