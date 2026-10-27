/**
 * HeroGraph — decorative skill-graph illustration for the landing page.
 *
 * Purely presentational: it is hidden from assistive technology because the
 * surrounding copy already explains the workflow. Animations respect
 * `prefers-reduced-motion` through the global stylesheet.
 */
export default function HeroGraph() {
  return (
    <div className="hero-visual" aria-hidden="true">
      <div className="hero-glow" />
      <svg
        className="hero-graph"
        viewBox="0 0 420 420"
        role="presentation"
        focusable="false"
      >
        <defs>
          <linearGradient id="coreGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#7c6cff" />
            <stop offset="55%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>

        {/* Connections between satellite nodes and the core */}
        <g>
          <line className="edge" x1="210" y1="210" x2="70" y2="88" />
          <line className="edge" x1="210" y1="210" x2="345" y2="78" />
          <line className="edge-active" x1="210" y1="210" x2="372" y2="205" />
          <line className="edge" x1="210" y1="210" x2="300" y2="330" />
          <line className="edge-active" x1="210" y1="210" x2="175" y2="360" />
          <line className="edge" x1="210" y1="210" x2="55" y2="285" />
          <line className="edge" x1="140" y1="150" x2="70" y2="88" opacity="0.55" />
          <line className="edge" x1="300" y1="330" x2="372" y2="205" opacity="0.4" />
          <line className="edge" x1="175" y1="360" x2="55" y2="285" opacity="0.35" />
        </g>

        {/* Satellite nodes */}
        <g>
          <circle className="node" cx="70" cy="88" r="20" />
          <text className="label" x="70" y="124" textAnchor="middle">Profile</text>

          <circle className="node" cx="345" cy="78" r="18" />
          <text className="label" x="345" y="112" textAnchor="middle">GitHub</text>

          <circle className="node-hot" cx="372" cy="205" r="22" />
          <text className="label" x="372" y="243" textAnchor="middle">Target role</text>

          <circle className="node" cx="300" cy="330" r="20" />
          <text className="label" x="300" y="366" textAnchor="middle">Skills</text>

          <circle className="node-hot" cx="175" cy="360" r="19" />
          <text className="label" x="175" y="395" textAnchor="middle">Roadmap</text>

          <circle className="node" cx="55" cy="285" r="19" />
          <text className="label" x="55" y="320" textAnchor="middle">Mentors</text>

          <circle className="node" cx="140" cy="150" r="13" />
          <text className="label-dim" x="140" y="178" textAnchor="middle">Resume</text>
        </g>

        {/* Core */}
        <circle className="edge" cx="210" cy="210" r="58" opacity="0.45" />
        <circle className="edge" cx="210" cy="210" r="82" opacity="0.18" />
        <circle className="node-core pulse" cx="210" cy="210" r="38" />
        <text x="210" y="207" textAnchor="middle" fill="#ffffff" fontSize="13" fontWeight="700">
          Your
        </text>
        <text x="210" y="223" textAnchor="middle" fill="#e0e7ff" fontSize="11" fontWeight="500">
          graph
        </text>

        {/* Accent particles */}
        <circle className="pulse-slow" cx="120" cy="70" r="2.4" fill="#a5b4fc" opacity="0.7" />
        <circle className="pulse-slow" cx="390" cy="300" r="2.2" fill="#22d3ee" opacity="0.6" />
        <circle className="pulse" cx="35" cy="170" r="2" fill="#8b5cf6" opacity="0.7" />
      </svg>
    </div>
  )
}
