import { useEffect, useState } from "react";
import { listTools } from "../api";

function DeveloperPage() {
  const [tools, setTools] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    listTools()
      .then((data) => {
        if (!cancelled) setTools(data.tools || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="content">
      <p className="page-intro">
        The live tool catalog straight from the deployed backend
        (GET /api/tools) — every tool listed here is callable over plain
        REST (used by this UI) or over the Model Context Protocol at
        /api/mcp (used by Claude Desktop, Claude Code, or any other MCP
        client — no REST wrapper needed).
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">API REFERENCE</span>
            <h3>Available tools</h3>
          </div>
        </div>

        {error && <p className="form-error">Couldn't load the tool catalog: {error}</p>}

        {!tools && !error && <p className="empty-state">Loading...</p>}

        {tools && tools.length === 0 && (
          <p className="empty-state">No tools registered.</p>
        )}

        {tools && tools.map((tool) => (
          <div className="tool-doc" key={tool.name}>
            <strong>{tool.name}</strong>
            <p>{tool.description}</p>
            <code>{`curl -X POST /api/tool/${tool.name} \\\n  -H "Content-Type: application/json" \\\n  -d '{ ... }'`}</code>
          </div>
        ))}
      </div>
    </section>
  );
}

export default DeveloperPage;
