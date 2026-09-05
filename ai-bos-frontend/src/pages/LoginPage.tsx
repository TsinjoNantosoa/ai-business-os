import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, AlertCircle, Loader2, Eye, EyeOff, Workflow, ShieldCheck, BarChart3 } from 'lucide-react';
import { useAuth } from '@/lib/auth/store';
import { useI18n } from '@/lib/i18n/store';
import {
  exchangeOAuthCode,
  getOAuthProviders,
  mockOAuthLogin,
  startOAuth,
} from '@/lib/api/services';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardFooter } from '@/components/ui/card';
import { Logo } from '@/components/layout/Logo';
import { DemoPersonaSelector } from '@/components/auth/DemoPersonaSelector';

export function LoginPage() {
  const { login, applyAuthResponse, isLoading, error } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [demoMode, setDemoMode] = useState(searchParams.get('demo') === 'true');
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);
  const [oauthModes, setOauthModes] = useState<Record<string, string>>({});

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/app/dashboard';

  useEffect(() => {
    void getOAuthProviders()
      .then((providers) => {
        setOauthModes(Object.fromEntries(providers.map((provider) => [provider.id, provider.mode])));
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const oauthCode = searchParams.get('oauth_code');
    if (oauthCode) {
      void (async () => {
        try {
          setOauthLoading(searchParams.get('oauth') || 'oauth');
          const response = await exchangeOAuthCode(oauthCode);
          await applyAuthResponse(response);
          navigate(from, { replace: true });
        } catch (err) {
          useAuth.setState({ error: err instanceof Error ? err.message : 'OAuth error' });
          navigate('/login', { replace: true });
        } finally {
          setOauthLoading(null);
        }
      })();
    }
  }, [searchParams, applyAuthResponse, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch {
      // error is in store
    }
  };

  const handleDemoLogin = async (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('demo1234');
    try {
      await login(demoEmail, 'demo1234');
      navigate(from, { replace: true });
    } catch {
      // error is in store
    }
  };

  const handleOAuth = async (provider: 'google' | 'microsoft') => {
    setOauthLoading(provider);
    try {
      const start = await startOAuth(provider);
      if (start.mode === 'mock') {
        const res = await mockOAuthLogin(provider, start.state, 'ceo@demo.aibos.io');
        await applyAuthResponse(res);
        navigate(from, { replace: true });
      } else {
        window.location.href = start.authorizationUrl;
      }
    } catch (err) {
      useAuth.setState({ error: err instanceof Error ? err.message : 'OAuth error' });
    } finally {
      setOauthLoading(null);
    }
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Left panel — branding */}
      <div className="relative hidden w-[48%] flex-col justify-between overflow-hidden border-r border-sidebar-border bg-sidebar p-12 lg:flex">
        <div className="absolute inset-0 opacity-25">
          <div className="absolute left-1/4 top-1/4 h-96 w-96 rounded-full bg-primary blur-[110px]" />
          <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-blue-600/40 blur-[120px]" />
        </div>
        <div className="relative z-10">
          <Logo />
        </div>
        <div className="relative z-10 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <p className="mb-4 text-xs font-semibold uppercase tracking-[.14em] text-primary-300">AI Business Operating System</p>
            <h1 className="max-w-xl text-4xl font-bold leading-[1.1] tracking-[-.035em] text-white xl:text-5xl">
              Le système d&apos;exploitation intelligent de votre entreprise.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">
              Unifiez vos données, automatisez vos opérations et prenez de meilleures décisions grâce à vos agents IA.
            </p>
          </motion.div>
          <div className="flex flex-wrap gap-x-6 gap-y-3">
            {[
              { icon: Sparkles, label: 'AI Copilot' },
              { icon: Workflow, label: 'Orchestration' },
              { icon: ShieldCheck, label: 'Approbations' },
              { icon: BarChart3, label: 'Insights temps réel' },
            ].map((f, i) => (
              <motion.div
                key={f.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className="flex items-center gap-2 text-sm text-slate-300"
              >
                <f.icon className="h-4 w-4 text-primary-400" />
                {f.label}
              </motion.div>
            ))}
          </div>
        </div>
        <div className="relative z-10 text-2xs text-slate-500">
          AI BOS · Données protégées · Contrôle humain
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex w-full items-center justify-center px-5 py-10 sm:p-8 lg:w-[52%]">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-2xl font-bold tracking-tight">{t('auth.welcomeBack')}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t('auth.loginSubtitle')}</p>
          </motion.div>

          <Card className="mt-6 border-border/80 shadow-elevated">
            <form onSubmit={handleSubmit}>
              <CardHeader className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">{t('auth.email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="vous@entreprise.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">{t('auth.password')}</Label>
                    <Link to="/forgot-password" className="text-xs text-primary hover:underline">
                      {t('auth.forgotPassword')}
                    </Link>
                  </div>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      autoComplete="current-password"
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-1 top-1 flex h-8 w-8 items-center justify-center rounded-sm text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                {error && (
                  <div role="alert" aria-live="polite" className="flex items-center gap-2 rounded-md border border-red-500/25 bg-red-500/[.08] px-3 py-2 text-sm text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {t('auth.invalidCredentials')}
                  </div>
                )}
              </CardHeader>
              <CardFooter className="flex-col gap-3">
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('auth.signIn')}
                </Button>
                <p className="text-center text-sm text-muted-foreground">
                  {t('auth.noAccount')}{' '}
                  <Link to="/register" className="font-medium text-primary hover:underline">
                    {t('auth.createAccount')}
                  </Link>
                </p>
                <div className="grid w-full grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={!!oauthLoading || oauthModes.google === 'disabled'}
                    onClick={() => void handleOAuth('google')}
                  >
                    {oauthLoading === 'google' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Google'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={!!oauthLoading || oauthModes.microsoft === 'disabled'}
                    onClick={() => void handleOAuth('microsoft')}
                  >
                    {oauthLoading === 'microsoft' ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Microsoft'}
                  </Button>
                </div>
                <p className="text-center text-2xs text-muted-foreground">
                  {Object.values(oauthModes).some((mode) => mode === 'live')
                    ? 'Connexion sécurisée avec votre compte Google ou Microsoft'
                    : 'OAuth en mode mock (sans credentials) → connexion CEO démo'}
                </p>
              </CardFooter>
            </form>
          </Card>

          {/* Demo accounts */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center">
                <button
                  type="button"
                  onClick={() => setDemoMode((value) => !value)}
                  className="relative bg-background px-3 text-xs font-medium text-muted-foreground hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {demoMode ? 'Masquer la démo' : 'Explorer la démo'}
                </button>
              </div>
            </div>
            {demoMode && (
              <div className="mt-4">
                <DemoPersonaSelector onSelect={(demoEmail) => void handleDemoLogin(demoEmail)} loading={isLoading} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
