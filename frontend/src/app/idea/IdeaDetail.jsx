import React from 'react';

const IdeaDetail = () => {
  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Page title */}
      <h1 className="text-4xl font-light">Bias-aware clinical triage system</h1>

      {/* Domain tag and novelty score */}
      <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4 flex items-center gap-4 max-w-xl">
        <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Healthcare</span>
        <div className="flex-1 max-w-xs">
          <div className="text-sm text-neutral-400">Novelty score</div>
          <div className="mt-1 w-full bg-neutral-700 rounded-full h-1">
            <div className="bg-neutral-400 h-1 rounded-full" style={{width: '82%'}}></div>
          </div>
        </div>
      </div>

      <div className="mt-12 h-px bg-neutral-800" />

      {/* Summary section */}
      <section className="mt-12">
        <h2 className="text-lg font-medium text-neutral-200">Summary</h2>
        <p className="mt-4 text-neutral-400">
          A machine learning system for clinical triage that incorporates bias detection and mitigation techniques to ensure equitable patient outcomes across diverse demographics. The system analyzes patient data, historical outcomes, and fairness metrics to prioritize cases while minimizing algorithmic bias.
        </p>
      </section>

      {/* Evidence sources section */}
      <section className="mt-12">
        <h2 className="text-lg font-medium text-neutral-200">Evidence sources</h2>
        <div className="mt-4 flex gap-2">
          <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">arXiv</span>
          <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">GitHub</span>
          <span className="px-2 py-1 text-xs bg-neutral-800 text-neutral-300 rounded">Prior ideas</span>
        </div>
      </section>

      {/* Evidence & confidence section */}
      <section className="mt-12">
        <h2 className="text-lg font-medium text-neutral-200">Evidence & confidence</h2>
        <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 max-w-xl">
          <p className="text-sm text-neutral-400">
            This idea was synthesized from multiple research signals and prior work. <span className="text-neutral-300">Novelty reflects relative differentiation within the system, not absolute originality.</span> All outputs are reviewed to surface uncertainty and reduce overconfidence.
          </p>
        </div>
      </section>

      {/* Feedback section */}
      <section className="mt-12">
        <h2 className="text-lg font-medium text-neutral-200">Feedback</h2>
        <div className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-6">
          <p className="text-sm text-neutral-400">
            Feedback is used to audit model behavior and improve future outputs. It does not immediately modify this result.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 px-3 py-1 text-sm">
              Accurate
            </button>
            <button className="rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 px-3 py-1 text-sm">
              Hallucinated
            </button>
            <button className="rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 px-3 py-1 text-sm">
              Weak novelty
            </button>
            <button className="rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 px-3 py-1 text-sm">
              Poor justification
            </button>
          </div>
          <textarea
            className="mt-4 w-full rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 p-3 text-sm placeholder-neutral-500"
            placeholder="Optional — add context or references…"
            rows="3"
          ></textarea>
          <button className="mt-4 rounded-md border border-neutral-800 bg-neutral-900/60 text-neutral-300 px-4 py-2 text-sm">
            Submit feedback
          </button>
        </div>
      </section>

      {/* Conceptual breakdown section */}
      <section className="mt-12">
        <h2 className="text-lg font-medium text-neutral-200">Conceptual breakdown</h2>
        <div className="mt-4 space-y-4">
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
            <h3 className="text-sm font-medium text-neutral-200">Bias detection</h3>
            <p className="mt-2 text-sm text-neutral-400">
              Identification of systematic patterns in data that may lead to unfair treatment across different demographic groups. This involves analyzing input features and model outputs for disproportionate impacts.
            </p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
            <h3 className="text-sm font-medium text-neutral-200">Triage prioritization</h3>
            <p className="mt-2 text-sm text-neutral-400">
              Ordering of patient cases based on urgency and resource availability. This component evaluates clinical indicators alongside fairness constraints to determine processing sequence.
            </p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
            <h3 className="text-sm font-medium text-neutral-200">Fairness metrics</h3>
            <p className="mt-2 text-sm text-neutral-400">
              Quantitative measures of equity in decision-making processes. These metrics assess balance across protected attributes while maintaining clinical accuracy standards.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default IdeaDetail;
