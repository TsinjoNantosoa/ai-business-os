import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AlertCircle, CheckCircle2, KeyRound, Loader2, LockKeyhole, Mail } from 'lucide-react';
import { resetPassword, verifyResetCode } from '@/lib/api/services';
import { useI18n } from '@/lib/i18n/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/layout/Logo';


type Step = 'code' | 'password' | 'done';

export function ResetPasswordPage() {
  const { t } = useI18n();
  const location = useLocation();
  const initialEmail = (location.state as { email?: string } | null)?.email ?? '';

  const [step, setStep] = useState<Step>('code');
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerifyCode = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await verifyResetCode(email, code.trim());
      setStep('password');
    } catch {
      setError(t('auth.invalidResetCode'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    if (password.length < 6) {
      setError(t('auth.passwordTooShort'));
      return;
    }
    if (password !== confirmation) {
      setError(t('auth.passwordMismatch'));
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      await resetPassword(email, code.trim(), password);
      setStep('done');
    } catch {
      setError(t('auth.invalidResetCode'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-6">
      <div className="w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <Card>
          <CardHeader>
            <CardTitle>{t('auth.resetTitle')}</CardTitle>
            <CardDescription>
              {step === 'code' ? t('auth.enterCodeSubtitle') : t('auth.resetSubtitle')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {step === 'done' && (
              <div className="space-y-5 text-center">
                <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-600" />
                <p className="text-sm text-muted-foreground">{t('auth.resetSuccess')}</p>
                <Button asChild className="w-full">
                  <Link to="/login">{t('auth.signIn')}</Link>
                </Button>
              </div>
            )}

            {step === 'code' && (
              <form className="space-y-4" onSubmit={handleVerifyCode}>
                <div className="space-y-2">
                  <Label htmlFor="reset-email">{t('auth.email')}</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="reset-email"
                      type="email"
                      autoComplete="email"
                      className="pl-9"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      required
                      autoFocus={!initialEmail}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reset-code">{t('auth.verificationCode')}</Label>
                  <div className="relative">
                    <KeyRound className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="reset-code"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      placeholder="123456"
                      className="pl-9 tracking-[0.3em]"
                      value={code}
                      onChange={(event) => setCode(event.target.value)}
                      minLength={4}
                      maxLength={16}
                      required
                      autoFocus={Boolean(initialEmail)}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">{t('auth.codeHint')}</p>
                </div>
                {error && (
                  <p className="flex items-center gap-2 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {error}
                  </p>
                )}
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('auth.verifyCode')}
                </Button>
                <Button asChild variant="ghost" className="w-full">
                  <Link to="/forgot-password">{t('auth.requestNewLink')}</Link>
                </Button>
              </form>
            )}

            {step === 'password' && (
              <form className="space-y-4" onSubmit={handleResetPassword}>
                <div className="space-y-2">
                  <Label htmlFor="new-password">{t('auth.newPassword')}</Label>
                  <div className="relative">
                    <LockKeyhole className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="new-password"
                      type="password"
                      autoComplete="new-password"
                      className="pl-9"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      minLength={6}
                      required
                      autoFocus
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">{t('auth.confirmPassword')}</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    autoComplete="new-password"
                    value={confirmation}
                    onChange={(event) => setConfirmation(event.target.value)}
                    minLength={6}
                    required
                  />
                </div>
                {error && (
                  <p className="flex items-center gap-2 text-sm text-destructive">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {error}
                  </p>
                )}
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('auth.resetPassword')}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
