import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { PageHeader } from '@/components/shared/PageHeader';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { initials } from '@/lib/utils';
import { exportGdprData } from '@/lib/api/services';
import { Download, Loader2 } from 'lucide-react';

export function SettingsProfilePage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const data = await exportGdprData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `aibos-gdpr-export-${user?.id || 'me'}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export impossible');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <PageHeader title={t('nav.settingsProfile')} description="Gérez votre profil et préférences" />
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader><CardTitle className="text-base">Informations personnelles</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                <AvatarFallback className="bg-primary-100 text-lg font-medium text-primary-700">
                  {user ? initials(`${user.firstName} ${user.lastName}`) : '?'}
                </AvatarFallback>
              </Avatar>
              <Button variant="outline">Changer la photo</Button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Prénom</Label><Input defaultValue={user?.firstName} /></div>
              <div className="space-y-2"><Label>Nom</Label><Input defaultValue={user?.lastName} /></div>
              <div className="space-y-2"><Label>Email</Label><Input defaultValue={user?.email} /></div>
              <div className="space-y-2"><Label>Téléphone</Label><Input defaultValue={user?.phone} /></div>
              <div className="space-y-2"><Label>Poste</Label><Input defaultValue={user?.jobTitle} /></div>
              <div className="space-y-2"><Label>Département</Label><Input defaultValue={user?.department} /></div>
            </div>
            <Button>{t('common.save')}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Sécurité</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2"><Label>Mot de passe actuel</Label><Input type="password" placeholder="••••••••" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Nouveau mot de passe</Label><Input type="password" placeholder="••••••••" /></div>
              <div className="space-y-2"><Label>Confirmer</Label><Input type="password" placeholder="••••••••" /></div>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Authentification à deux facteurs</p>
                <p className="text-xs text-muted-foreground">Sécurisez votre compte avec un code temporaire</p>
              </div>
              <Switch defaultChecked={user?.twoFactorEnabled} />
            </div>
            <Button>{t('common.save')}</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base">Confidentialité (GDPR)</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Exportez une copie JSON de vos données (droit à la portabilité).
            </p>
            {exportError && <p className="text-sm text-destructive">{exportError}</p>}
            <Button variant="outline" onClick={() => void handleExport()} disabled={exporting}>
              {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              Exporter mes données
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
