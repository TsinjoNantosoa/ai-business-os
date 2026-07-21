import { useEffect, useState } from 'react';
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
import { changePassword, exportGdprData, requestGdprErase, updateProfile } from '@/lib/api/services';
import { Download, Loader2, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

export function SettingsProfilePage() {
  const { user, setUser } = useAuth();
  const { t } = useI18n();
  const [firstName, setFirstName] = useState(user?.firstName || '');
  const [lastName, setLastName] = useState(user?.lastName || '');
  const [savingProfile, setSavingProfile] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [erasing, setErasing] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
  }, [user?.firstName, user?.lastName]);

  const handleSaveProfile = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      toast.error('Prénom et nom requis');
      return;
    }
    setSavingProfile(true);
    try {
      const updated = await updateProfile({
        firstName: firstName.trim(),
        lastName: lastName.trim(),
      });
      setUser({ ...user!, ...updated });
      toast.success('Profil mis à jour');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Impossible de sauvegarder');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSavePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error('Renseignez les mots de passe');
      return;
    }
    if (newPassword.length < 6) {
      toast.error('Le nouveau mot de passe doit faire au moins 6 caractères');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('La confirmation ne correspond pas');
      return;
    }
    setSavingPassword(true);
    try {
      await changePassword({ currentPassword, newPassword });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Mot de passe modifié');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Impossible de changer le mot de passe');
    } finally {
      setSavingPassword(false);
    }
  };

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
      toast.success('Export GDPR téléchargé');
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export impossible');
    } finally {
      setExporting(false);
    }
  };

  const handleErase = async () => {
    if (!window.confirm('Confirmer la demande d’effacement GDPR ? Cette action lance une procédure de suppression.')) {
      return;
    }
    setErasing(true);
    setExportError(null);
    try {
      const res = await requestGdprErase();
      toast.success(`Demande d’effacement enregistrée (${res.status})`);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Demande impossible');
      toast.error(err instanceof Error ? err.message : 'Demande impossible');
    } finally {
      setErasing(false);
    }
  };

  return (
    <div>
      <PageHeader title={t('nav.settingsProfile')} description="Gérez votre profil et préférences" />
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations personnelles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Avatar className="h-20 w-20">
                <AvatarFallback className="bg-primary-100 text-lg font-medium text-primary-700">
                  {user ? initials(`${firstName} ${lastName}`) : '?'}
                </AvatarFallback>
              </Avatar>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Prénom</Label>
                <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label>Nom</Label>
                <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
              <div className="col-span-2 space-y-2">
                <Label>Email</Label>
                <Input value={user?.email || ''} disabled />
              </div>
            </div>
            <Button disabled={savingProfile} onClick={() => void handleSaveProfile()}>
              {savingProfile && <Loader2 className="h-4 w-4 animate-spin" />}
              {t('common.save')}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sécurité</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Mot de passe actuel</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Nouveau mot de passe</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Confirmer</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Authentification à deux facteurs</p>
                <p className="text-xs text-muted-foreground">Non disponible côté API pour le moment</p>
              </div>
              <Switch disabled defaultChecked={user?.twoFactorEnabled} />
            </div>
            <Button disabled={savingPassword} onClick={() => void handleSavePassword()}>
              {savingPassword && <Loader2 className="h-4 w-4 animate-spin" />}
              Changer le mot de passe
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Confidentialité (GDPR)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Exportez une copie JSON de vos données (droit à la portabilité) ou demandez l’effacement.
            </p>
            {exportError && <p className="text-sm text-destructive">{exportError}</p>}
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => void handleExport()} disabled={exporting || erasing}>
                {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                Exporter mes données
              </Button>
              <Button
                variant="outline"
                className="text-destructive"
                onClick={() => void handleErase()}
                disabled={exporting || erasing}
              >
                {erasing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                Demander l’effacement
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
