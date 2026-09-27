import { Icon } from '../components/Icon'
import { navigate } from '../router'

const capabilities = [
  ['Delay Risk Prediction', 'Estimate potential acquisition-delay risk from the current project record.', 'analytics'],
  ['Explainable AI', 'Show the operational factors contributing to a risk assessment.', 'recommendations'],
  ['Smart Recommendations', 'Translate assessed risk signals into structured officer actions.', 'check'],
  ['Early Alerts', 'Surface high-priority project conditions for timely review.', 'alerts'],
  ['What-If Simulation', 'Compare a project baseline with non-persistent improvement scenarios.', 'whatif'],
  ['GIS Monitoring', 'View assessed project locations in a spatial portfolio view.', 'location'],
  ['Analytics', 'Track portfolio-level risk, status, stage, and attention indicators.', 'dashboard'],
  ['PDF Reports', 'Generate a project report from the currently stored records.', 'document'],
]

const flow = [
  ['01', 'Project Data', 'Officer-maintained project and acquisition information.'],
  ['02', 'ML Risk Prediction', 'The saved model estimates delay-risk probability.'],
  ['03', 'SHAP Explanation', 'Risk contributors are presented for officer review.'],
  ['04', 'Action Recommendations', 'Deterministic rules create practical next steps.'],
  ['05', 'Alerts & Escalation', 'Structured alert records prioritize urgent issues.'],
  ['06', 'What-If Analysis', 'Changes can be compared without overwriting the project.'],
]

export function HomePage() {
  return <main className="home-page">
    <header className="home-nav">
      <button className="home-brand" type="button" onClick={() => navigate('/')} aria-label="BhoomiGuard AI home"><span>BG</span><div><b>BhoomiGuard AI</b><small>Land acquisition intelligence</small></div></button>
      <div><button className="home-nav-link" type="button" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>How it works</button><button className="secondary-button" type="button" onClick={() => navigate('/login')}>Officer login</button></div>
    </header>

    <section className="home-hero">
      <div className="home-hero-copy"><p className="home-eyebrow"><Icon name="location" size={15} />Decision support for land acquisition</p><h1>Predict. Explain.<br /><em>Prevent.</em></h1><p className="home-lede">BhoomiGuard AI helps officers identify potential land-acquisition delays early, understand the contributing factors, and organise timely operational action.</p><div className="home-actions"><button className="primary-button home-primary" type="button" onClick={() => navigate('/login')}>Start Monitoring Projects <Icon name="arrowRight" size={16} /></button><button className="home-text-action" type="button" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>Explore how it works <Icon name="arrowDown" size={16} /></button></div><p className="home-note">Explainable predictive decision-support. Officer judgement remains essential.</p></div>
      <div className="home-hero-panel" aria-label="BhoomiGuard assessment flow"><div className="land-grid" /><div className="hero-panel-label">Portfolio intelligence</div><div className="hero-metric"><span>Assessment pathway</span><b>Project → Risk → Action</b></div><div className="hero-signal"><i /><div><b>Early-warning signal</b><small>Assessment is linked to stored project evidence</small></div></div><div className="hero-stage-list"><span>Compensation</span><span>Documentation</span><span>Approvals</span><span>Legal / ownership</span></div></div>
    </section>

    <section className="home-section home-problem"><div><p className="home-eyebrow">The operational challenge</p><h2>Land acquisition delays rarely have one cause.</h2></div><p>Projects move through documentation, compensation, rehabilitation, resettlement, approvals, legal review, and coordination. BhoomiGuard AI is designed to identify risk signals before they become a completed delay—not merely report them afterwards.</p></section>

    <section className="home-section" id="how-it-works"><div className="home-section-heading"><p className="home-eyebrow">How it works</p><h2>From project record to accountable action.</h2><p>Each stage builds on the existing project record and keeps the assessment traceable.</p></div><div className="home-flow">{flow.map(([number, title, description]) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div></section>

    <section className="home-section home-capabilities"><div className="home-section-heading"><p className="home-eyebrow">Core capabilities</p><h2>One operational workspace.</h2></div><div className="home-capability-grid">{capabilities.map(([title, description, icon]) => <article key={title}><Icon name={icon} size={20} /><h3>{title}</h3><p>{description}</p></article>)}</div></section>

    <section className="home-section home-workflow"><div><p className="home-eyebrow">Officer workflow</p><h2>A clear path from record to reassessment.</h2></div><ol><li>Create or import project</li><li>Assess risk</li><li>Understand drivers</li><li>Take action</li><li>Monitor progress</li><li>Reassess</li></ol></section>

    <section className="home-section home-trust"><div><p className="home-eyebrow">Technology and trust</p><h2>Built for transparent decision support.</h2><p>React and FastAPI deliver the application workflow; PostgreSQL stores operational records; scikit-learn Logistic Regression estimates delay risk; SHAP explains model contributions; MapLibre and OpenStreetMap provide portfolio mapping.</p></div><aside><Icon name="info" size={19} /><p>The current ML prototype is trained and evaluated on synthetic data. Authorized real-world data, governance, and external validation are required before production deployment.</p></aside></section>

    <section className="home-cta"><div><p className="home-eyebrow">BhoomiGuard AI</p><h2>Start monitoring projects with earlier, clearer signals.</h2></div><button className="primary-button home-primary" type="button" onClick={() => navigate('/login')}>Start Monitoring Projects <Icon name="arrowRight" size={16} /></button></section>
    <footer className="home-footer">BhoomiGuard AI · Explainable land-acquisition decision support</footer>
  </main>
}
