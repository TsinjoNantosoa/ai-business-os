import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardFooter, CardHeader } from '@/components/ui/card';
import { Logo } from '@/components/layout/Logo';

export function RegisterPage() {
  const { register, isLoading, error } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [organizationName, setOrganizationName] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (password.length < 6) {
      setLocalError(t('auth.passwordTooShort'));
      return;
    }
    if (password !== confirmPassword) {
      setLocalError(t('auth.passwordMismatch'));
      return;
    }
    try {
      await register({
        email: email.trim(),
        password,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        organizationName: organizationName.trim(),
      });
      navigate('/onboarding', { replace: true });
    } catch {
      // error is in store
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      <div className="relative hidden w-[48%] flex-col justify-between overflow-hidden border-r border-sidebar-border bg-sidebar p-12 lg:flex">
        <div className="absolute inset-0 opacity-25">
          <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-primary blur-[110px]" />
          <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-600/40 blur-[120px]" />
        </div>
        <div className="relative z-10">
          <Logo />
        </div>
        <div className="relative z-10 space-y-4">
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-xl text-4xl font-bold leading-[1.1] tracking-[-.035em] text-white xl:text-5xl"
          >
            Créez votre espace
            <br />
            AI BOS
          </motion.h1>
          <p className="max-w-lg text-base leading-7 text-slate-400">
            Créez votre organisation, centralisez vos opérations et gardez le contrôle sur chaque action proposée par vos agents IA.
          </p>
        </div>
        <div className="relative z-10 text-2xs text-slate-500">AI BOS · Données protégées · Contrôle humain</div>
      </div>

      <div className="flex w-full items-center justify-center px-5 py-10 sm:p-8 lg:w-[52%]">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <h2 className="text-2xl font-bold tracking-tight">{t('auth.signUpTitle')}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{t('auth.signUpSubtitle')}</p>

          <Card className="mt-6 border-border/80 shadow-elevated">
            <form onSubmit={(e) => void handleSubmit(e)}>
              <CardHeader className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="org">{t('auth.organizationName')}</Label>
                  <Input
                    id="org"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="Acme SAS"
                    required
                    autoComplete="organization"
                  />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">{t('auth.firstName')}</Label>
                    <Input
                      id="firstName"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                      autoComplete="given-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">{t('auth.lastName')}</Label>
                    <Input
                      id="lastName"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      required
                      autoComplete="family-name"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">{t('auth.email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="vous@entreprise.com"
                    required
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">{t('auth.password')}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm">{t('auth.confirmPassword')}</Label>
                  <Input
                    id="confirm"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </div>
                {(localError || error) && (
                  <div role="alert" aria-live="polite" className="flex items-center gap-2 rounded-md border border-red-500/25 bg-red-500/[.08] px-3 py-2 text-sm text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {localError || error}
                  </div>
                )}
              </CardHeader>
              <CardFooter className="flex-col gap-3">
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('auth.createAccount')}
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  {t('auth.alreadyHaveAccount')}{' '}
                  <Link to="/login" className="font-medium text-primary hover:underline">
                    {t('auth.signIn')}
                  </Link>
                </p>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
