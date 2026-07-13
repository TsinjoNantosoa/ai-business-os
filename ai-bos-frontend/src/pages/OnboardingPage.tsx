import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Building2, Users, Plug, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Logo } from '@/components/layout/Logo';
import { useI18n } from '@/lib/i18n/store';
import { createInvitation, getMyOrganization, updateMyOrganization } from '@/lib/api/services';

const STEPS = [
  { icon: Building2, title: 'Informations entreprise', description: 'Configurez votre organisation' },
  { icon: Users, title: "Inviter l'équipe", description: 'Ajoutez vos collaborateurs' },
  { icon: Plug, title: 'Connecter les intégrations', description: 'Liez vos outils préférés' },
];

export function OnboardingPage() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orgName, setOrgName] = useState('');
  const [currency, setCurrency] = useState('EUR');
  const [timezone, setTimezone] = useState('Europe/Paris');
  const [address, setAddress] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteSent, setInviteSent] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const org = await getMyOrganization();
        if (cancelled) return;
        setOrgName(org.name || '');
        setCurrency(org.currency || 'EUR');
        setTimezone(org.timezone || 'Europe/Paris');
        setAddress(org.address || '');
      } catch {
        if (!cancelled) setError("Impossible de charger l'organisation");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleFinish = () => {
    navigate('/app/dashboard');
  };

  const handleNext = async () => {
    setError(null);
    if (step === 0) {
      setSaving(true);
      try {
        await updateMyOrganization({
          name: orgName.trim() || undefined,
          currency: currency.trim() || undefined,
          timezone: timezone.trim() || undefined,
          address: address.trim() || undefined,
        });
        setStep(1);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
      } finally {
        setSaving(false);
      }
      return;
    }
    if (step === 1) {
      if (inviteEmail.trim()) {
        setSaving(true);
        try {
          await createInvitation({ email: inviteEmail.trim(), role: 'staff' });
          setInviteSent(true);
          setStep(2);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Erreur lors de l'invitation");
        } finally {
          setSaving(false);
        }
        return;
      }
      setStep(2);
      return;
    }
    handleFinish();
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border bg-card px-6 py-4">
        <Logo />
      </div>
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="mb-10 flex items-center justify-between">
          {STEPS.map((s, i) => (
            <div key={i} className="flex items-center">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-xl transition-colors ${
                  i <= step ? 'bg-primary text-white' : 'bg-muted text-muted-foreground'
                }`}
              >
                {i < step ? <Check className="h-5 w-5" /> : <s.icon className="h-5 w-5" />}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`mx-2 h-0.5 w-16 rounded-full ${i < step ? 'bg-primary' : 'bg-muted'}`} />
              )}
            </div>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            <h1 className="text-2xl font-bold">{STEPS[step].title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{STEPS[step].description}</p>

            <Card className="mt-6">
              <CardContent className="space-y-4 p-6">
                {step === 0 && (
                  <>
                    <div className="space-y-2">
                      <Label>Nom de l'entreprise</Label>
                      <Input placeholder="Acme Corp" value={orgName} onChange={(e) => setOrgName(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Devise</Label>
                        <Input placeholder="EUR" value={currency} onChange={(e) => setCurrency(e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <Label>Fuseau horaire</Label>
                        <Input placeholder="Europe/Paris" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Adresse</Label>
                      <Input placeholder="123 rue de la Paix, 75001 Paris" value={address} onChange={(e) => setAddress(e.target.value)} />
                    </div>
                  </>
                )}
                {step === 1 && (
                  <>
                    <div className="space-y-2">
                      <Label>Inviter par email</Label>
                      <Input
                        type="email"
                        placeholder="collegue@entreprise.com"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                      />
                    </div>
                    {inviteSent && (
                      <p className="text-sm text-emerald-600">Invitation créée (lien disponible via l’API / email mock).</p>
                    )}
                    <p className="text-sm text-muted-foreground">
                      Vous pourrez ajouter plus de membres plus tard depuis les paramètres.
                    </p>
                  </>
                )}
                {step === 2 && (
                  <div className="space-y-3">
                    {['Slack', 'Google Workspace', 'Stripe', 'Zapier'].map((tool) => (
                      <div key={tool} className="flex items-center justify-between rounded-lg border border-border p-3">
                        <span className="text-sm font-medium">{tool}</span>
                        <Button variant="outline" size="sm" type="button">
                          Connecter
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                {error && <p className="text-sm text-destructive">{error}</p>}
              </CardContent>
            </Card>

            <div className="mt-6 flex justify-between">
              <Button
                variant="outline"
                onClick={() => (step > 0 ? setStep(step - 1) : navigate('/app/dashboard'))}
                disabled={saving}
              >
                <ArrowLeft className="h-4 w-4" />
                {step > 0 ? t('common.previous') : t('common.skip')}
              </Button>
              <Button onClick={handleNext} disabled={saving}>
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                {step < 2 ? t('common.next') : t('common.confirm')}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
