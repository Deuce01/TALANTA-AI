// Neo4j Initialization Script
// Run this once to set up the graph database schema and seed data

// ==================== Constraints ====================

CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT skill_name IF NOT EXISTS
FOR (s:Skill) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT job_id IF NOT EXISTS
FOR (j:Job) REQUIRE j.id IS UNIQUE;

CREATE CONSTRAINT location_name IF NOT EXISTS
FOR (l:Location) REQUIRE l.name IS UNIQUE;

// ==================== Indexes ====================

CREATE INDEX user_trust_score IF NOT EXISTS
FOR (u:User) ON (u.trust_score);

CREATE INDEX skill_category IF NOT EXISTS
FOR (s:Skill) ON (s.category);

CREATE INDEX job_active IF NOT EXISTS
FOR (j:Job) ON (j.is_active);

// ==================== Seed Skills Taxonomy ====================

// Construction Skills
CREATE (plumbing:Skill {name: 'Plumbing', category: 'Construction', complexity: 2});
CREATE (electrical:Skill {name: 'Electrical Wiring', category: 'Construction', complexity: 3});
CREATE (solar:Skill {name: 'Solar Installation', category: 'Renewable Energy', complexity: 3});
CREATE (carpentry:Skill {name: 'Carpentry', category: 'Construction', complexity: 2});
CREATE (masonry:Skill {name: 'Masonry', category: 'Construction', complexity: 2});
CREATE (painting:Skill {name: 'Painting', category: 'Construction', complexity: 1});

// Manufacturing & Trades
CREATE (welding:Skill {name: 'Welding', category: 'Manufacturing', complexity: 3});
CREATE (metalwork:Skill {name: 'Metal Fabrication', category: 'Manufacturing', complexity: 3});

// Automotive
CREATE (mechanic:Skill {name: 'Automotive Repair', category: 'Automotive', complexity: 3});
CREATE (driving:Skill {name: 'Driving', category: 'Transport', complexity: 1});

// Beauty & Fashion
CREATE (hairdressing:Skill {name: 'Hairdressing', category: 'Beauty', complexity: 1});
CREATE (tailoring:Skill {name: 'Tailoring', category: 'Fashion', complexity: 2});

// Technology
CREATE (ict:Skill {name: 'Computer Literacy', category: 'Technology', complexity: 1});
CREATE (networking:Skill {name: 'Networking', category: 'Technology', complexity: 3});

// ==================== Skill Prerequisites ====================

MATCH (basic:Skill {name: 'Electrical Wiring'})
MATCH (advanced:Skill {name: 'Solar Installation'})
CREATE (basic)-[:PREREQUISITE_FOR]->(advanced);

MATCH (basic:Skill {name: 'Driving'})
MATCH (advanced:Skill {name: 'Automotive Repair'})
CREATE (basic)-[:PREREQUISITE_FOR]->(advanced);

MATCH (basic:Skill {name: 'Computer Literacy'})
MATCH (advanced:Skill {name: 'Networking'})
CREATE (basic)-[:PREREQUISITE_FOR]->(advanced);

// ==================== Seed Locations ====================

CREATE (nairobi:Location {name: 'Nairobi', county: 'Nairobi', lat: -1.286389, long: 36.817223});
CREATE (mombasa:Location {name: 'Mombasa', county: 'Mombasa', lat: -4.043477, long: 39.668206});
CREATE (kisumu:Location {name: 'Kisumu', county: 'Kisumu', lat: -0.091702, long: 34.767956});
CREATE (nakuru:Location {name: 'Nakuru', county: 'Nakuru', lat: -0.303099, long: 36.080026});
CREATE (eldoret:Location {name: 'Eldoret', county: 'Uasin Gishu', lat: 0.514277, long: 35.269779});

// ==================== Success Message ====================

RETURN 'Neo4j database initialized successfully!' AS message;
