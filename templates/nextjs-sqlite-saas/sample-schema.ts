/**
 * Reference Drizzle ORM Schema for SQLite SaaS Architecture.
 * Demonstrates proper primary keys, foreign key indexes, timestamps, and relations.
 */

import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core";
import { relations } from "drizzle-orm";

export const users = sqliteTable("users", {
  id: text("id").primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
  avatarUrl: text("avatar_url"),
  role: text("role", { enum: ["owner", "admin", "member"] }).default("member").notNull(),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
});

export const teams = sqliteTable("teams", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  slug: text("slug").notNull().unique(),
  ownerId: text("owner_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
}, (table) => ({
  ownerIdx: index("teams_owner_id_idx").on(table.ownerId),
}));

export const subscriptions = sqliteTable("subscriptions", {
  id: text("id").primaryKey(),
  teamId: text("team_id").notNull().unique().references(() => teams.id, { onDelete: "cascade" }),
  stripeCustomerId: text("stripe_customer_id").notNull().unique(),
  stripeSubscriptionId: text("stripe_subscription_id").unique(),
  plan: text("plan", { enum: ["free", "pro", "enterprise"] }).default("free").notNull(),
  status: text("status", { enum: ["active", "trialing", "past_due", "canceled"] }).default("active").notNull(),
  currentPeriodEnd: integer("current_period_end").notNull(),
  createdAt: text("created_at").notNull(),
}, (table) => ({
  teamIdx: index("subscriptions_team_id_idx").on(table.teamId),
}));

export const auditLogs = sqliteTable("audit_logs", {
  id: text("id").primaryKey(),
  teamId: text("team_id").notNull().references(() => teams.id, { onDelete: "cascade" }),
  userId: text("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  action: text("action").notNull(),
  ipAddress: text("ip_address"),
  metadata: text("metadata"), // JSON stringified
  createdAt: text("created_at").notNull(),
}, (table) => ({
  teamTimeIdx: index("audit_logs_team_time_idx").on(table.teamId, table.createdAt),
}));

// Drizzle Relations
export const usersRelations = relations(users, ({ many }) => ({
  ownedTeams: many(teams),
  auditLogs: many(auditLogs),
}));

export const teamsRelations = relations(teams, ({ one, many }) => ({
  owner: one(users, { fields: [teams.ownerId], references: [users.id] }),
  subscription: one(subscriptions),
  auditLogs: many(auditLogs),
}));
