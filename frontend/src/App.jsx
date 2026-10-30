import React, { useEffect, useState } from "react";

const documents = [
  ["employee_handbook", "Employee handbook"],
  ["leave_policy", "Leave policy"],
  ["work_from_home", "Work from home"],
  ["travel_policy", "Travel expenses"],
  ["information_security", "Information security"],
  ["code_of_conduct", "Code of conduct"],
];

const examples = [
  "How much annual leave can employees take?",
  "What is the work from home policy?",
  "Who is covered by the employee handbook?",
];

async function apiRequest(path, payload) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 65000);
  try {
    const response = await fetch(`/api/${path}`, {
      method: payload ? "POST" : "GET",
      headers: payload ? { "Content-Type": "application/json" } : undefined,
      body: payload ? JSON.stringify(payload) : undefined,
      signal: controller.signal,
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof result.detail === "string" ? result.detail : "The request could not be completed.";
      throw new Error(detail);
    }
    return result;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Please try again.");
    }
    if (error instanceof TypeError) {
      throw new Error("Could not reach PolicyLens. Check your connection and try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

function formatSource(source = "Policy document") {
  return source
    .replace(/^documents[\\/]/i, "")
    .replace(/\.pdf$/i, "")
    .replaceAll("_", " ");
}

function App() {
  const [activeView, setActiveView] = useState("ask");
  const [backendOnline, setBackendOnline] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [askError, setAskError] = useState("");
  const [asking, setAsking] = useState(false);
  const [document1, setDocument1] = useState(documents[0][0]);
  const [document2, setDocument2] = useState(documents[1][0]);
  const [topic, setTopic] = useState("");
  const [comparison, setComparison] = useState(null);
  const [compareError, setCompareError] = useState("");
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    let active = true;
    const check = () => {
      apiRequest("health/ready")
        .then(() => active && setBackendOnline(true))
        .catch(() => active && setBackendOnline(false));
    };
    check();
    const interval = window.setInterval(check, 30000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const evaluationId = answer?.evaluation?.evaluation_id;
    if (!evaluationId || answer.evaluation.evaluation_status !== "pending") return undefined;

    let active = true;
    let failures = 0;
    let timer;
    const pollEvaluation = async () => {
      try {
        const evaluation = await apiRequest(`evaluation/${evaluationId}`);
        if (!active) return;
        failures = 0;
        setAnswer((current) => (
          current?.evaluation?.evaluation_id === evaluationId
            ? { ...current, evaluation }
            : current
        ));
        if (evaluation.evaluation_status === "pending") {
          timer = window.setTimeout(pollEvaluation, 1500);
        }
      } catch {
        if (!active) return;
        failures += 1;
        if (failures >= 3) {
          setAnswer((current) => (
            current?.evaluation?.evaluation_id === evaluationId
              ? {
                  ...current,
                  evaluation: {
                    ...current.evaluation,
                    evaluation_status: "unavailable",
                    evaluation_error: "Evaluation status could not be retrieved.",
                  },
                }
              : current
          ));
        } else {
          timer = window.setTimeout(pollEvaluation, 3000);
        }
      }
    };
    timer = window.setTimeout(pollEvaluation, 1500);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [answer?.evaluation?.evaluation_id, answer?.evaluation?.evaluation_status]);

  async function submitQuestion(event) {
    event.preventDefault();
    if (!question.trim() || asking) return;
    setAsking(true);
    setAskError("");
    setAnswer(null);
    try {
      setAnswer(await apiRequest("ask", { question: question.trim() }));
    } catch (error) {
      setAskError(error.message);
    } finally {
      setAsking(false);
    }
  }

  async function submitComparison(event) {
    event.preventDefault();
    if (!topic.trim() || comparing) return;
    if (document1 === document2) {
      setCompareError("Choose two different documents to compare.");
      return;
    }
    setComparing(true);
    setCompareError("");
    setComparison(null);
    try {
      const result = await apiRequest("contradict", {
        document1,
        document2,
        topic: topic.trim(),
      });
      setComparison(result.result);
    } catch (error) {
      setCompareError(error.message);
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="PolicyLens home">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>Policy<span className="brand-light">Lens</span></span>
        </a>
        <div className="topbar-meta">
          <span className={`status-dot ${backendOnline === false ? "offline" : ""}`} />
          <span>{backendOnline === null ? "Connecting" : backendOnline ? "All systems ready" : "Service unavailable"}</span>
        </div>
      </header>

      <main className="main-content">
        <section className="intro">
          <p className="eyebrow">POLICY INTELLIGENCE</p>
          <h1>Clarity, grounded in your documents.</h1>
          <p className="intro-copy">
            Ask a question or compare policies. Every answer is based on your source documents.
          </p>
        </section>

        <div className="workspace">
          <nav className="tabs" aria-label="Workspace">
            <button
              className={`tab ${activeView === "ask" ? "selected" : ""}`}
              onClick={() => setActiveView("ask")}
              type="button"
            >
              Ask documents
            </button>
            <button
              className={`tab ${activeView === "compare" ? "selected" : ""}`}
              onClick={() => setActiveView("compare")}
              type="button"
            >
              Compare policies
            </button>
          </nav>

          {activeView === "ask" ? (
            <section className="panel" aria-labelledby="ask-heading">
              <div className="panel-heading">
                <div>
                  <h2 id="ask-heading">Ask your documents</h2>
                  <p>Get a concise answer with citations to the original policy.</p>
                </div>
                <span className="source-label"><span className="source-dot" /> Policy library</span>
              </div>

              <form onSubmit={submitQuestion}>
                <label className="sr-only" htmlFor="question">Your question</label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  maxLength={2000}
                  placeholder="What would you like to know?"
                  rows={4}
                />
                <div className="form-footer">
                  <span className="input-hint">Answers are grounded in the indexed policies.</span>
                  <button className="primary-button" disabled={!question.trim() || asking} type="submit">
                    {asking ? <><span className="spinner" /> Searching</> : <>Ask PolicyLens <span aria-hidden="true">→</span></>}
                  </button>
                </div>
              </form>

              {!answer && !askError && (
                <div className="suggestions">
                  <span className="suggestions-label">Try asking</span>
                  {examples.map((example) => (
                    <button className="suggestion" key={example} onClick={() => setQuestion(example)} type="button">
                      {example}
                    </button>
                  ))}
                </div>
              )}

              {askError && <p className="notice error-notice" role="alert">{askError}</p>}

              {answer && (
                <div className="result" aria-live="polite">
                  <div className="result-title">
                    <span className="result-icon" aria-hidden="true">✦</span>
                    <h3>Answer</h3>
                  </div>
                  <p className="answer-text">{answer.answer}</p>
                  <div className="citation-heading">
                    <h3>Sources</h3>
                    <span>{answer.citations?.length ?? 0} cited {(answer.citations?.length ?? 0) === 1 ? "passage" : "passages"}</span>
                  </div>
                  {answer.citations?.length ? (
                    <div className="citations">
                      {answer.citations.map((citation, index) => (
                        <article className="citation" key={`${citation.chunk ?? citation.id ?? index}-${index}`}>
                          <div className="citation-meta">
                            <span className="citation-number">[{citation.id ?? index + 1}]</span>
                            <span className="citation-source">{formatSource(citation.source)}</span>
                            <span className="citation-page">Page {citation.page ?? "—"}</span>
                          </div>
                          {citation.snippet && <p>{citation.snippet}</p>}
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="empty-sources">No supporting passages were retrieved.</p>
                  )}
                  {answer.evaluation?.evaluation_status === "completed" && (
                    <div className="evaluation-summary">
                      <div className="citation-heading">
                        <h3>Live RAG evaluation</h3>
                        <span>LLM judge · runs after the answer</span>
                      </div>
                      <div className="evaluation-metrics">
                        {[
                          ["Faithfulness", answer.evaluation.faithfulness],
                          ["Answer relevancy", answer.evaluation.answer_relevancy],
                          ["Context relevancy", answer.evaluation.context_relevancy],
                        ].map(([label, score]) => (
                          <div className="evaluation-metric" key={label}>
                            <span>{label}</span>
                            <strong>{score == null ? "—" : `${Math.round(score * 100)}%`}</strong>
                          </div>
                        ))}
                      </div>
                      <p className="evaluation-latency">
                        Evaluation completed in {answer.evaluation.evaluation_latency_seconds ?? "—"} sec.
                      </p>
                    </div>
                  )}
                  {answer.evaluation?.evaluation_status === "pending" && (
                    <p className="evaluation-pending" role="status">
                      Your answer is ready. RAG evaluation is running in the background and will be added to the Excel report.
                    </p>
                  )}
                  {answer.evaluation?.evaluation_status === "unavailable" && (
                    <p className="notice error-notice" role="status">
                      Answer returned, but RAG evaluation was unavailable: {answer.evaluation.evaluation_error}
                    </p>
                  )}
                  {answer.evaluation?.report_error && (
                    <p className="notice error-notice" role="status">
                      Evaluation report could not be updated: {answer.evaluation.report_error}
                    </p>
                  )}
                </div>
              )}
            </section>
          ) : (
            <section className="panel" aria-labelledby="compare-heading">
              <div className="panel-heading">
                <div>
                  <h2 id="compare-heading">Compare policies</h2>
                  <p>Check two documents for conflicting guidance on a topic.</p>
                </div>
              </div>
              <form onSubmit={submitComparison}>
                <div className="select-grid">
                  <label>
                    <span>First document</span>
                    <select value={document1} onChange={(event) => setDocument1(event.target.value)}>
                      {documents.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </label>
                  <label>
                    <span>Second document</span>
                    <select value={document2} onChange={(event) => setDocument2(event.target.value)}>
                      {documents.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                    </select>
                  </label>
                </div>
                <label className="topic-label" htmlFor="topic">Topic to compare</label>
                <input
                  id="topic"
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  maxLength={200}
                  placeholder="For example, remote work eligibility"
                />
                <div className="form-footer">
                  <span className="input-hint">The comparison uses only retrieved policy excerpts.</span>
                  <button className="primary-button" disabled={!topic.trim() || comparing} type="submit">
                    {comparing ? <><span className="spinner" /> Comparing</> : <>Compare policies <span aria-hidden="true">→</span></>}
                  </button>
                </div>
              </form>
              {compareError && <p className="notice error-notice" role="alert">{compareError}</p>}
              {comparison && (
                <div className="result comparison-result" aria-live="polite">
                  <div className="result-title">
                    <span className={`result-icon ${comparison.conflict === true ? "conflict-icon" : comparison.conflict === null ? "unknown-icon" : ""}`} aria-hidden="true">
                      {comparison.conflict === true ? "!" : comparison.conflict === false ? "✓" : "?"}
                    </span>
                    <h3>{comparison.conflict === true ? "Potential contradiction found" : comparison.conflict === false ? "No contradiction found" : "Not enough evidence"}</h3>
                  </div>
                  <p className="answer-text">{comparison.reason}</p>
                </div>
              )}
            </section>
          )}
        </div>

        <footer className="page-footer">
          <span>PolicyLens</span>
          <span>Grounded answers. Clear sources.</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
