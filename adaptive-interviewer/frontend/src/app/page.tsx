import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <div className="mb-2 font-mono text-sm uppercase tracking-widest text-darpan-lime">
        Darpan Labs · Adaptive Interviewer
      </div>
      <h1 className="text-4xl font-semibold md:text-5xl">
        60-minute adaptive interview for digital-twin capture.
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-neutral-400">
        One conversation — universal preamble, silent archetype classification,
        archetype-specific JTBD/conjoint/brand/tone blocks, universal
        personality and values tail. Produces a structured per-respondent
        output object for product and ad concept simulation.
      </p>

      <div className="mt-10 flex gap-4">
        <Link
          href="/interview"
          className="inline-flex items-center rounded-lg border border-darpan-lime bg-darpan-lime/10 px-6 py-3 font-medium text-darpan-lime shadow-glow-lime transition hover:bg-darpan-lime/20"
        >
          Start an interview
        </Link>
        <a
          href="http://localhost:8002/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center rounded-lg border border-darpan-border px-6 py-3 text-neutral-300 transition hover:border-darpan-border-active"
        >
          API docs
        </a>
      </div>

      <footer className="mt-20 text-sm text-neutral-500">
        v1 · laptop category · three archetypes (prosumer / SMB IT / consumer)
      </footer>
    </main>
  );
}
