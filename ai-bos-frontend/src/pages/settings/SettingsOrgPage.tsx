import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PageHeader } from '@/components/shared/PageHeader';
import { getMyOrganization, updateMyOrganization } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { toast } from 'sonner';

export function SettingsOrgPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { data: org, isLoading, error } = useQuery({
    queryKey: ['organization', 'me'],
    queryFn: getMyOrganization,
  });

  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [currency, setCurrency] = useState('EUR');
  const [timezone, setTimezone] = useState('Europe/Paris');
  const [locale, setLocale] = useState('fr');

  useEffect(() => {
    if (!org) return;
    setName(org.name || '');
    setAddress(org.address || '');
    setCurrency(org.currency || 'EUR');
    setTimezone(org.timezone || 'Europe/Paris');
    setLocale(org.locale || 'fr');
  }, [org]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateMyOrganization({
        name: name.trim(),
        address: address.trim() || undefined,
        currency,
        timezone,
        locale,
      }),
    onSuccess: (updated) => {
      void queryClient.setQueryData(['organization', 'me'], updated);
      toast.success('Organisation enregistrée');
    },
    onError: (err: Error) => toast.error(err.message || "Impossible d'enregistrer l'organisation"),
  });

  const initial = org?.name?.[0]?.toUpperCase() || 'A';

  return (
    <div>
      <PageHeader title={t('nav.settingsOrg')} description="Configurez votre organisation" />
      <div className="max-w-2xl space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations générales</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Chargement…
              </div>
            ) : error ? (
              <p className="text-sm text-destructive">{error instanceof Error ? error.message : 'Erreur de chargement'}</p>
            ) : (
              <>
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl gradient-ai">
                    <span className="text-xl font-bold text-white">{initial}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Plan <span className="font-medium capitalize text-foreground">{org?.plan}</span>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-name">Nom de l&apos;organisation</Label>
                  <Input id="org-name" value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-address">Adresse</Label>
                  <Input
                    id="org-address"
                    placeholder="123 rue de la Paix"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Devise</Label>
                    <Select value={currency} onValueChange={setCurrency}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="USD">USD</SelectItem>
                        <SelectItem value="GBP">GBP</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Fuseau horaire</Label>
                    <Select value={timezone} onValueChange={setTimezone}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Europe/Paris">Europe/Paris</SelectItem>
                        <SelectItem value="America/New_York">America/New_York</SelectItem>
                        <SelectItem value="UTC">UTC</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Langue</Label>
                    <Select value={locale} onValueChange={setLocale}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fr">Français</SelectItem>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="ar">العربية</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  disabled={saveMutation.isPending || !name.trim()}
                  onClick={() => saveMutation.mutate()}
                >
                  {saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  {t('common.save')}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
