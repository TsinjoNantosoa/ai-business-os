import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

/** Avoid importing the full auth store (and API services) on the landing critical path. */
function usePersistedToken(): string | null {
  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    try {
      const raw = localStorage.getItem('aibos-auth');
      if (!raw) return;
      const parsed = JSON.parse(raw) as { state?: { token?: string | null } };
      setToken(parsed.state?.token ?? null);
    } catch {
      /* ignore */
    }
  }, []);
  return token;
}

/**
 * Public first impression at `/`.
 * No framer-motion / lucide / auth-store on this route — keeps first paint light for Lighthouse.
 */
export function LandingPage() {
  const navigate = useNavigate();
  const token = usePersistedToken();

  useEffect(() => {
    if (token) navigate('/app/dashboard', { replace: true });
  }, [token, navigate]);

  return (
    <div className="landing-root relative min-h-screen overflow-hidden text-[#e8efe9]">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[#06120f]" />
        <div className="landing-grid absolute inset-0 opacity-[0.35]" />
        <div className="landing-glow absolute -left-1/4 top-[-20%] h-[70vh] w-[70vw] rounded-full bg-[#1faa7a]/[0.18] blur-[100px]" />
        <div className="landing-glow-delay absolute -right-1/4 bottom-[-10%] h-[55vh] w-[55vw] rounded-full bg-[#c8f542]/[0.08] blur-[110px]" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#06120f]" />
      </div>

      <header className="relative z-10 flex items-center justify-between gap-3 px-4 py-4 sm:px-10 sm:py-5">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#c8f542] text-[#06120f]" aria-hidden>
            <svg viewBox="0 0 32 32" className="h-5 w-5" aria-hidden>
              <path d="M16 7L25 25H21.5L16 13L10.5 25H7L16 7Z" fill="currentColor" />
              <rect x="13" y="19" width="6" height="2.5" rx="1" fill="currentColor" />
            </svg>
          </span>
          <span className="font-[family-name:var(--landing-display)] text-lg font-bold tracking-tight text-white">
            AI BOS
          </span>
        </div>
        <Link
          to="/register"
          className="text-sm font-medium text-[#c5d9cc] transition hover:text-white"
        >
          Créer un compte
        </Link>
      </header>

      <main
        id="main"
        className="relative z-10 mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 px-4 pb-14 pt-4 sm:gap-12 sm:px-10 sm:pb-16 sm:pt-6 lg:grid-cols-2 lg:gap-10 lg:pb-20"
      >
        <div className="landing-fade-up">
          <p className="font-[family-name:var(--landing-display)] text-[clamp(3rem,9vw,5.75rem)] font-extrabold leading-[0.9] tracking-tight text-white">
            AI BOS
          </p>

          <h1 className="mt-5 font-[family-name:var(--landing-display)] text-[clamp(1.35rem,3vw,1.9rem)] font-semibold leading-snug text-[#f2f7f3]">
            Le système d&apos;exploitation intelligent de votre entreprise
          </h1>

          <p className="mt-4 max-w-md text-base leading-relaxed text-[#b7cfc2] sm:text-lg">
            Une seule couche pour décider, orchestrer et exécuter — métiers et agents AI
            synchronisés en temps réel.
          </p>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link
              to="/register"
              className="group inline-flex min-h-11 items-center gap-2 rounded-full bg-[#c8f542] px-7 py-3.5 text-sm font-semibold text-[#06120f] shadow-[0_0_40px_-8px_rgba(200,245,66,0.55)] transition hover:bg-[#d4f76a]"
            >
              Commencer gratuitement
              <svg className="h-4 w-4 transition group-hover:translate-x-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <path d="M5 12h14M13 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <Link
              to="/login"
              className="inline-flex min-h-11 items-center gap-2 rounded-full border border-white/25 px-6 py-3.5 text-sm font-medium text-[#f2f7f3] transition hover:border-white/40 hover:bg-white/5"
            >
              Se connecter
            </Link>
          </div>
        </div>

        <div
          className="landing-fade-in relative min-h-[280px] sm:min-h-[360px]"
          aria-hidden
        >
          <div className="landing-orbit absolute left-1/2 top-1/2 h-[115%] w-[115%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#1faa7a]/20" />
          <div className="absolute inset-0 overflow-hidden rounded-none border border-white/10 bg-[#0a1a15]/75 shadow-[0_40px_100px_-40px_rgba(0,0,0,0.85)] backdrop-blur-sm lg:rounded-l-[2rem] lg:border-r-0">
            <div className="flex items-center gap-2 border-b border-white/10 px-5 py-3">
              <span className="h-1.5 w-1.5 rounded-full bg-[#c8f542]" />
              <span className="text-[11px] tracking-[0.16em] text-[#a8c0b2] uppercase">
                core · live
              </span>
            </div>
            <div className="space-y-6 p-6 sm:p-8">
              <div>
                <p className="font-[family-name:var(--landing-display)] text-3xl font-bold text-white sm:text-4xl">
                  Orchestration
                </p>
                <p className="mt-2 max-w-sm text-sm leading-relaxed text-[#a8c0b2]">
                  Le Copilot aligne CRM, finance et opérations sur une seule vérité.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  { label: 'Flux métier', width: '78%' },
                  { label: 'Agents AI', width: '92%' },
                  { label: 'Décisions', width: '64%' },
                ].map((row, i) => (
                  <div key={row.label}>
                    <div className="mb-1.5 flex justify-between text-xs text-[#a8c0b2]">
                      <span>{row.label}</span>
                    </div>
                    <div className="h-1 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="landing-bar h-full rounded-full bg-[#1faa7a]"
                        style={{
                          ['--bar-width' as string]: row.width,
                          animationDelay: `${0.35 + i * 0.12}s`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      <style>{`
        .landing-root {
          --landing-display: 'Syne', system-ui, sans-serif;
          font-family: 'Figtree', system-ui, sans-serif;
        }
        .landing-grid {
          background-image:
            linear-gradient(rgba(200, 245, 66, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(200, 245, 66, 0.06) 1px, transparent 1px);
          background-size: 64px 64px;
          mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, #000 20%, transparent 75%);
        }
        .landing-glow { animation: landingPulse 8s ease-in-out infinite; }
        .landing-glow-delay { animation: landingPulse 10s ease-in-out infinite reverse; }
        .landing-orbit { animation: landingSpin 48s linear infinite; }
        .landing-fade-up {
          animation: landingFadeUp 0.55s ease-out both;
        }
        .landing-fade-in {
          animation: landingFadeIn 0.7s ease-out 0.1s both;
        }
        .landing-bar {
          width: 0;
          animation: landingBar 1.1s ease-out forwards;
        }
        @keyframes landingPulse {
          0%, 100% { opacity: 0.55; transform: scale(1); }
          50% { opacity: 0.9; transform: scale(1.06); }
        }
        @keyframes landingSpin {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to { transform: translate(-50%, -50%) rotate(360deg); }
        }
        @keyframes landingFadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes landingFadeIn {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes landingBar {
          to { width: var(--bar-width); }
        }
        @media (prefers-reduced-motion: reduce) {
          .landing-glow, .landing-glow-delay, .landing-orbit,
          .landing-fade-up, .landing-fade-in, .landing-bar {
            animation: none !important;
          }
          .landing-bar { width: var(--bar-width); }
          .landing-fade-up, .landing-fade-in { opacity: 1; transform: none; }
        }
      `}</style>
    </div>
  );
}
