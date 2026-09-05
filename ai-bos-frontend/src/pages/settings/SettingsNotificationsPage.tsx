import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/shared/PageHeader';
import { useI18n } from '@/lib/i18n/store';
import { AlertTriangle, BarChart3, Calendar, CheckSquare, CreditCard, FileText, MessageSquare, Target } from 'lucide-react';

const CHANNELS = ['Email', 'SMS', 'Push', 'Slack'] as const;
const CATEGORIES = [
  { name: 'Factures et paiements', icon: CreditCard },
  { name: 'Nouveaux leads', icon: Target },
  { name: 'Tâches assignées', icon: CheckSquare },
  { name: 'Réunions', icon: Calendar },
  { name: 'Alertes système', icon: AlertTriangle },
  { name: 'Rapports hebdo', icon: BarChart3 },
  { name: 'Mentions', icon: MessageSquare },
  { name: 'Contrats', icon: FileText },
];

export function SettingsNotificationsPage() {
  const { t } = useI18n();
  const [prefs, setPrefs] = useState(() =>
    Object.fromEntries(
      CATEGORIES.flatMap((cat) =>
        CHANNELS.map((c) => [`${cat.name}:${c}`, Math.random() > 0.3] as const),
      ),
    ) as Record<string, boolean>,
  );

  const toggle = (key: string) => {
    setPrefs((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div>
      <PageHeader
        title={t('nav.settingsNotifications')}
        description="Configurez vos préférences de notification"
      />

      {/* Mobile: stacked cards */}
      <div className="space-y-3 md:hidden">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          return <Card key={cat.name}>
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary" aria-hidden><Icon className="h-4 w-4" /></span>
                <p className="text-sm font-medium">{cat.name}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {CHANNELS.map((c) => {
                  const key = `${cat.name}:${c}`;
                  return (
                    <div key={c} className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2">
                      <Label htmlFor={key} className="text-xs text-muted-foreground">
                        {c}
                      </Label>
                      <Switch id={key} checked={!!prefs[key]} onCheckedChange={() => toggle(key)} />
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>;
        })}
      </div>

      {/* Tablet+: matrix table */}
      <Card className="hidden md:block">
        <CardContent className="p-0">
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full min-w-[36rem]">
              <thead>
                <tr className="border-b border-border">
                  <th className="p-4 text-left text-sm font-medium">Type de notification</th>
                  {CHANNELS.map((c) => (
                    <th key={c} className="p-4 text-center text-sm font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATEGORIES.map((cat) => {
                  const Icon = cat.icon;
                  return <tr key={cat.name} className="border-b border-border">
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary" aria-hidden><Icon className="h-4 w-4" /></span>
                        <span className="text-sm font-medium">{cat.name}</span>
                      </div>
                    </td>
                    {CHANNELS.map((c) => {
                      const key = `${cat.name}:${c}`;
                      return (
                        <td key={c} className="p-4 text-center">
                          <Switch checked={!!prefs[key]} onCheckedChange={() => toggle(key)} />
                        </td>
                      );
                    })}
                  </tr>;
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
