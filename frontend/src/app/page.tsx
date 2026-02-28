import Link from "next/link";
import { User, FlaskConical, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      {/* Hero */}
      <div className="text-center mb-16">
        <h1 className="text-5xl font-bold mb-4">
          <span className="text-darpan-lime">Darpan</span>{" "}
          <span className="text-white">Labs</span>
        </h1>
        <p className="text-xl text-gray-400">
          AI-powered digital twins for consumer research
        </p>
      </div>

      {/* Side selector cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl w-full">
        {/* Creator side */}
        <Link
          href="/create/modules"
          className="group relative p-8 rounded-2xl bg-darpan-surface border border-darpan-border
                   hover:border-darpan-lime/50 transition-all hover:shadow-glow-lime"
        >
          <div className="w-14 h-14 rounded-xl bg-darpan-lime/10 flex items-center justify-center mb-6">
            <User className="w-7 h-7 text-darpan-lime" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            I want to make my Twin
          </h2>
          <p className="text-white/50 mb-6">
            Build your digital twin through AI-powered interviews. Complete 4 short modules and generate your AI persona.
          </p>
          <span className="inline-flex items-center gap-2 text-darpan-lime font-medium text-sm group-hover:gap-3 transition-all">
            Get Started
            <ArrowRight className="w-4 h-4" />
          </span>
        </Link>

        {/* Brand side */}
        <Link
          href="/brand/experiments"
          className="group relative p-8 rounded-2xl bg-darpan-surface border border-darpan-border
                   hover:border-darpan-cyan/50 transition-all hover:shadow-glow-cyan"
        >
          <div className="w-14 h-14 rounded-xl bg-darpan-cyan/10 flex items-center justify-center mb-6">
            <FlaskConical className="w-7 h-7 text-darpan-cyan" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            I am a Brand
          </h2>
          <p className="text-white/50 mb-6">
            Run experiments and generate insights from digital twins. Test scenarios against cohorts instantly.
          </p>
          <span className="inline-flex items-center gap-2 text-darpan-cyan font-medium text-sm group-hover:gap-3 transition-all">
            Go to Experiments
            <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-8 text-center text-gray-500 text-sm">
        <p>Digital Twin Platform</p>
      </footer>
    </main>
  );
}
