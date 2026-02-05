import React from "react";

const GenerateResult = ({ result, error }) => {
  if (error) {
    return (
      <div className="border border-yellow-700 bg-yellow-950/20 p-4 rounded-md max-w-3xl">
        <p className="text-sm text-yellow-300">{error}</p>
      </div>
    );
  }

  const { idea, novelty_score } = result;

  return (
    <section className="space-y-10 max-w-3xl">
      <header>
        <h1 className="text-2xl text-white font-medium">{idea.title}</h1>
        <p className="text-sm text-gray-400 mt-2">Novelty score: {novelty_score}</p>
      </header>

      <section>
        <h2 className="text-lg text-white mb-2">Problem</h2>
        <p className="text-gray-300">{idea.problem_formulation.context}</p>
      </section>

      <section>
        <h2 className="text-lg text-white mb-2">Proposed contribution</h2>
        <p className="text-gray-300">{idea.proposed_contribution.core_idea}</p>
      </section>

      <section>
        <h2 className="text-lg text-white mb-4">System / project design</h2>
        <ul className="space-y-2">
          {idea.system_or_project_design.modules.map((module, idx) => (
            <li key={idx} className="text-gray-300">
              <strong>{module.name}:</strong> {module.responsibility}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-lg text-white mb-4">Evidence sources</h2>
        <ul className="space-y-3">
          {idea.evidence_sources.map((src) => (
            <li key={src.source_id} className="text-sm">
              <a
                href={src.url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:underline"
              >
                {src.title}
              </a>
              <div className="text-gray-500">{src.source_type}</div>
            </li>
          ))}
        </ul>
      </section>
    </section>
  );
};

export default GenerateResult;
