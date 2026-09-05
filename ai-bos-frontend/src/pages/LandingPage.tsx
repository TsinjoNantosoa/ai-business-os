import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function usePersistedToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    try {
      const raw = localStorage.getItem('aibos-auth');
      if (!raw) return;
      const parsed = JSON.parse(raw) as { state?: { token?: string | null } };
      setToken(parsed.state?.token ?? null);
    } catch { /* Storage may be unavailable. */ }
  }, []);
  return token;
}

const flow = [
  { label: 'Lead détecté', detail: 'Signal commercial', icon: 'signal' },
  { label: 'Sales Agent', detail: 'Qualifie et enrichit', icon: 'agent' },
  { label: 'CRM + Finance', detail: 'Contexte unifié', icon: 'data' },
  { label: 'Décision proposée', detail: 'Confiance 94 %', icon: 'decision' },
  { label: 'Approbation humaine', detail: 'Contrôle requis', icon: 'approval' },
];

function FlowIcon({ type }: { type: string }) {
  if (type === 'agent') return <path d="M8 9h8M8 13h5M12 3v2m-6 1-2-2m14 2 2-2M6 5h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />;
  if (type === 'data') return <path d="M4 7c0 1.1 3.6 2 8 2s8-.9 8-2-3.6-2-8-2-8 .9-8 2Zm0 0v5c0 1.1 3.6 2 8 2s8-.9 8-2V7m-16 5v5c0 1.1 3.6 2 8 2s8-.9 8-2v-5" />;
  if (type === 'decision') return <path d="m5 12 4 4L19 6" />;
  if (type === 'approval') return <path d="M12 3 5 6v5c0 4.6 3 8.2 7 10 4-1.8 7-5.4 7-10V6l-7-3Zm-3 9 2 2 4-4" />;
  return <path d="M4 12h4l2-6 4 12 2-6h4" />;
}

export function LandingPage() {
  const navigate = useNavigate();
  const token = usePersistedToken();
  useEffect(() => { if (token) navigate('/app/dashboard', { replace: true }); }, [token, navigate]);

  return (
    <div className="landing-root relative min-h-screen overflow-hidden bg-[#080d1a] text-[#f7f8fc]">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="landing-grid absolute inset-0 opacity-50" />
        <div className="landing-glow absolute -left-48 -top-48 h-[36rem] w-[36rem] rounded-full bg-[#6857ff]/15 blur-[110px]" />
        <div className="absolute bottom-[-18rem] right-[-10rem] h-[42rem] w-[42rem] rounded-full bg-[#4ea8ff]/[0.07] blur-[130px]" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#080d1a]" />
      </div>

      <header className="relative z-10 mx-auto flex max-w-[1440px] items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
        <Link to="/" className="flex items-center gap-3" aria-label="AI BOS — Accueil">
          <span className="flex h-9 w-9 items-center justify-center rounded-[10px] border border-[#8e80ff]/40 bg-[#6857ff]/15 text-[#9d91ff]" aria-hidden>
            <svg viewBox="0 0 24 24" className="h-5 w-5 fill-none stroke-current" strokeWidth="1.8"><path d="M12 3 20 7.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m8 14 4-7 4 7M9.5 11.5h5"/></svg>
          </span>
          <span className="text-base font-bold tracking-[-0.02em] text-white">AI BOS</span>
        </Link>
        <nav className="flex items-center gap-3" aria-label="Navigation principale">
          <Link to="/login" className="hidden rounded-md px-3 py-2 text-sm font-medium text-[#a7b3cc] transition-colors hover:text-white sm:inline-flex">Se connecter</Link>
          <Link to="/register" className="inline-flex h-10 items-center rounded-md bg-[#6857ff] px-4 text-sm font-semibold text-white shadow-[0_10px_28px_-16px_rgba(104,87,255,.9)] transition-colors hover:bg-[#5946e8]">Commencer</Link>
        </nav>
      </header>

      <main id="main" className="relative z-10 mx-auto grid min-h-[calc(100vh-5rem)] max-w-[1440px] items-center gap-14 px-5 pb-16 pt-10 sm:px-8 lg:grid-cols-[.92fr_1.08fr] lg:px-12 lg:pb-24 lg:pt-8">
        <div className="landing-fade-up max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#6857ff]/25 bg-[#6857ff]/10 px-3 py-1.5 text-xs font-semibold text-[#b7afff]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#19c891]" />
            AI Business Operating System
          </div>
          <p className="text-[clamp(3.8rem,9vw,7rem)] font-extrabold leading-[.82] tracking-[-.07em] text-white">AI BOS</p>
          <h1 className="mt-8 max-w-xl text-[clamp(1.8rem,3.5vw,3.15rem)] font-semibold leading-[1.08] tracking-[-.04em] text-[#f7f8fc]">
            L’entreprise, orchestrée par l’intelligence.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-[#a7b3cc] sm:text-lg">
            Unifiez vos données, coordonnez vos agents IA et transformez chaque décision en action — avec vos équipes toujours aux commandes.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link to="/register" className="group inline-flex min-h-11 items-center gap-2 rounded-md bg-[#6857ff] px-6 py-3 text-sm font-semibold text-white shadow-[0_14px_35px_-18px_rgba(104,87,255,.95)] transition-colors hover:bg-[#5946e8]">
              Commencer gratuitement
              <svg className="h-4 w-4 transition-transform group-hover:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M13 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </Link>
            <Link to="/login?demo=true" className="inline-flex min-h-11 items-center rounded-md border border-[#263249] bg-[#0f1628]/70 px-5 py-3 text-sm font-semibold text-[#dbe1ef] transition-colors hover:border-[#6857ff]/45 hover:bg-[#151e32]">Explorer la démo</Link>
          </div>
          <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-xs text-[#6f7d99]">
            <span>Multi-tenant</span><span>Contrôles humains</span><span>Données temps réel</span>
          </div>
        </div>

        <section className="landing-fade-in relative mx-auto w-full max-w-2xl" aria-label="Exemple d’orchestration AI BOS">
          <div aria-hidden className="absolute -inset-8 rounded-[2rem] bg-[#6857ff]/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-[18px] border border-[#263249] bg-[#0b1220]/95 shadow-[0_40px_100px_-44px_rgba(0,0,0,.95)]">
            <div className="flex items-center justify-between border-b border-[#263249] px-5 py-4">
              <div><p className="text-sm font-semibold text-white">Orchestration active</p><p className="mt-0.5 text-xs text-[#6f7d99]">Du signal à la décision contrôlée</p></div>
              <span className="inline-flex items-center gap-2 rounded-full border border-[#19c891]/20 bg-[#19c891]/10 px-2.5 py-1 text-[11px] font-semibold text-[#55ddb2]"><span className="h-1.5 w-1.5 rounded-full bg-[#19c891]" />Live</span>
            </div>
            <div className="p-5 sm:p-7">
              <div className="relative space-y-2">
                <div className="absolute bottom-7 left-[19px] top-7 w-px bg-gradient-to-b from-[#6857ff] via-[#4d5c78] to-[#19c891]/60" aria-hidden />
                {flow.map((step, index) => (
                  <div key={step.label} className="landing-node relative flex items-center gap-4 rounded-[10px] border border-transparent px-1 py-2.5 transition-colors hover:border-[#263249] hover:bg-[#0f1628]" style={{ animationDelay: `${.18 + index * .09}s` }}>
                    <div className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] border ${index === flow.length - 1 ? 'border-[#19c891]/30 bg-[#19c891]/10 text-[#55ddb2]' : 'border-[#6857ff]/30 bg-[#151e32] text-[#9d91ff]'}`}>
                      <svg viewBox="0 0 24 24" className="h-[18px] w-[18px] fill-none stroke-current" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><FlowIcon type={step.icon} /></svg>
                    </div>
                    <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-[#f7f8fc]">{step.label}</p><p className="mt-0.5 text-xs text-[#6f7d99]">{step.detail}</p></div>
                    <span className="text-[10px] font-semibold uppercase tracking-[.12em] text-[#596884]">{index < 3 ? 'automatique' : index === 3 ? 'proposé' : 'à valider'}</span>
                  </div>
                ))}
              </div>
              <div className="mt-5 flex items-center justify-between rounded-[10px] border border-[#6857ff]/25 bg-[#6857ff]/[.08] px-4 py-3">
                <div><p className="text-xs font-semibold text-[#b7afff]">Décision recommandée</p><p className="mt-1 text-sm text-white">Créer une séquence de suivi commercial</p></div>
                <span className="rounded-md bg-[#6857ff] px-3 py-1.5 text-xs font-semibold text-white">Approuver</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <style>{`
        .landing-grid{background-image:linear-gradient(rgba(104,87,255,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(104,87,255,.055) 1px,transparent 1px);background-size:64px 64px;mask-image:radial-gradient(ellipse 75% 70% at 50% 35%,#000 15%,transparent 78%)}
        .landing-glow{animation:landingPulse 9s ease-in-out infinite}.landing-fade-up{animation:landingFadeUp .55s ease-out both}.landing-fade-in{animation:landingFadeIn .65s ease-out .08s both}.landing-node{opacity:0;animation:landingNode .4s ease-out forwards}
        @keyframes landingPulse{50%{opacity:.72;transform:scale(1.05)}}@keyframes landingFadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}@keyframes landingFadeIn{from{opacity:0;transform:translateX(16px)}to{opacity:1;transform:none}}@keyframes landingNode{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
        @media(prefers-reduced-motion:reduce){.landing-glow,.landing-fade-up,.landing-fade-in,.landing-node{animation:none;opacity:1}}
      `}</style>
    </div>
  );
}
