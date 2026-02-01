import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="relative overflow-hidden">
      
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.15),transparent_40%)]" />

      {/* HERO */}
      <section className="relative max-w-7xl mx-auto px-6 pt-32 pb-32 grid md:grid-cols-2 gap-16 items-center">
        <div>
          <h1 className="text-5xl md:text-6xl font-light tracking-tight leading-tight">
            Project ideas
            <br />
            <span className="text-neutral-400">from research evidence.</span>
          </h1>

          <p className="mt-6 text-lg text-neutral-400 max-w-2xl">
            InnovateSphere generates project ideas from current research, multi-source novelty analysis, and human-reviewed quality signals.
          </p>

          <div className="mt-10 flex gap-4">
            <Link
              to="/explore"
              className="px-6 py-3 rounded-md bg-neutral-100 text-neutral-900 font-medium hover:bg-white transition"
            >
              Explore ideas
            </Link>
            <Link
              to="/register"
              className="px-6 py-3 rounded-md border border-neutral-700 text-neutral-200 hover:border-neutral-500 transition"
            >
              Sign up
            </Link>
          </div>
        </div>

        {/* Right visual placeholder */}
        <div className="hidden md:block relative">
          <div className="aspect-square rounded-xl border border-neutral-800 bg-neutral-900">
            <div className="p-6 flex flex-col justify-between h-full">
              <div>
                <div className="text-xs text-neutral-500 uppercase tracking-wide">Idea Preview</div>
                <h3 className="text-lg font-medium text-neutral-200 mt-2">Bias-aware clinical triage system</h3>
                <div className="mt-4">
                  <div className="text-sm text-neutral-400">Novelty score</div>
                  <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
                    <div className="bg-neutral-400 h-1 rounded-full" style={{width: '82%'}}></div>
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">arXiv</span>
                  <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">GitHub</span>
                  <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Prior ideas</span>
                </div>
              </div>
              <div className="text-xs text-neutral-500">Generated from live research and prior work</div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="relative max-w-7xl mx-auto px-6 py-28">
        <div className="grid md:grid-cols-3 gap-10">
          {[
            {
              title: 'Grounded in evidence',
              desc: 'Ideas from live research and signals, not fixed prompts.'
            },
            {
              title: 'Multi-source novelty',
              desc: 'Evaluated across papers, code, trends, and prior ideas.'
            },
            {
              title: 'Human-reviewed quality',
              desc: 'Outputs reviewed and refined to minimize errors.'
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
