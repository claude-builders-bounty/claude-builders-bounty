CREATE TABLE organizations (id TEXT PRIMARY KEY);
CREATE TABLE projects (
  id TEXT NOT NULL,
  organization_id TEXT NOT NULL REFERENCES organizations(id),
  name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
  PRIMARY KEY (organization_id, id)
);
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  organization_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  title TEXT NOT NULL,
  FOREIGN KEY (organization_id, project_id)
    REFERENCES projects(organization_id, id)
);
CREATE INDEX projects_by_organization ON projects(organization_id, name, id);
