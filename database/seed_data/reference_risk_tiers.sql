-- Reference data: operational action per risk tier (static documentation table).
CREATE TABLE IF NOT EXISTS ref_risk_tier_actions (
    tier   TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    rank   SMALLINT NOT NULL
);
INSERT INTO ref_risk_tier_actions (tier, action, rank) VALUES
    ('low', 'allow', 1),
    ('medium', 'step-up authentication', 2),
    ('high', 'hold for manual review', 3),
    ('critical', 'block + alert', 4)
ON CONFLICT (tier) DO NOTHING;
