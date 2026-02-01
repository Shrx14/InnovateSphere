import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="relative overflow-hidden">
      
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.15),transparent_40%)]" />

      {/* HERO */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-28 grid md:grid-cols-2 gap-16 items-center">
        <div>
          <h1 className="text-5xl md:text-6xl font-light tracking-tight leading-tight">
            Evidence-backed project ideas,
            <br />
            <span className="text-neutral-400">not guesses.</span>
          </h1>

          <p className="mt-6 text-lg text-neutral-400 max-w-xl">
            InnovateSphere helps students and builders explore project ideas grounded
            in real research, multi-source novelty analysis, and human-reviewed quality signals.
          </p>

          <div className="mt-10 flex gap-4">
            <Link
              to="/explore"
              className="px-6 py-3 rounded-md bg-neutral-100 text-neutral-900 font-medium hover:bg-white transition"
            >
              Try as guest
            </Link>
            <Link
              to="/register"
              className="px-6 py-3 rounded-md border border-neutral-700 text-neutral-200 hover:border-neutral-500 transition"
            >
              Get started
            </Link>
          </div>
        </div>

        {/* Right visual placeholder */}
        <div className="hidden md:block relative">
          <div className="aspect-square rounded-xl border border-neutral-800 bg-neutral-900 flex items-center justify-center text-neutral-600 text-sm">
            Live research + novelty signals
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="relative max-w-7xl mx-auto px-6 py-24">
        <div className="grid md:grid-cols-3 gap-10">
          {[
            {
              title: 'Grounded in evidence',
              desc: 'Ideas are generated using live research sources and real-world signals, not static prompts.'
            },
            {
              title: 'True novelty analysis',
              desc: 'Novelty is evaluated across papers, repositories, popularity, and prior ideas.'
            },
            {
              title: 'Human-in-the-loop quality',
              desc: 'Outputs are reviewed, rated, and corrected over time to reduce hallucination.'
            }
          ].map((item, i) => (
            <div
              key={i}
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-8"
            >
              <h3 className="text-lg font-medium">{item.title}</h3>
              <p className="mt-3 text-sm text-neutral-400">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* PROOF / PREVIEW */}
      <section className="relative max-w-7xl mx-auto px-6 pb-32">
        <div className="grid md:grid-cols-2 gap-16">
          <div>
            <h3 className="text-xl font-medium mb-4">Top domains</h3>
            <ul className="space-y-2 text-neutral-400 text-sm">
              <li>Artificial Intelligence</li>
              <li>Healthcare & Biotech</li>
              <li>Climate & Energy</li>
              <li>Fintech & Systems</li>
              <li>Human-Computer Interaction</li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-medium mb-4">Example ideas</h3>
            <ul className="space-y-2 text-neutral-400 text-sm">
              <li>Bias-aware clinical triage models</li>
              <li>Carbon-aware scheduling systems</li>
              <li>Explainable fraud detection pipelines</li>
              <li>AI-assisted curriculum generation</li>
              <li>Energy-efficient edge inference</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
