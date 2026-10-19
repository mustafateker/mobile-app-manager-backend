import Database from 'better-sqlite3';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

export type ManagedApp = {
  id: string;
  name: string;
  slug: string;
  iosBundleId: string | null;
  androidPackage: string | null;
  appStoreUrl: string | null;
  playStoreUrl: string | null;
  asoBeastAppId: string | null;
  color: string;
  status: 'development' | 'review' | 'live';
  createdAt: string;
  updatedAt: string;
};

export class AppDatabase {
  private readonly db: Database.Database;

  constructor(path: string) {
    mkdirSync(dirname(path), { recursive: true });
    this.db = new Database(path);
    this.db.pragma('journal_mode = WAL');
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS managed_apps (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE,
        ios_bundle_id TEXT,
        android_package TEXT,
        app_store_url TEXT,
        play_store_url TEXT,
        asobeast_app_id TEXT,
        color TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `);
    this.seed();
  }

  private seed() {
    const insert = this.db.prepare(`
      INSERT OR IGNORE INTO managed_apps
      (id, name, slug, ios_bundle_id, android_package, app_store_url, play_store_url, asobeast_app_id, color, status, created_at, updated_at)
      VALUES (@id, @name, @slug, @iosBundleId, @androidPackage, @appStoreUrl, @playStoreUrl, NULL, @color, @status, @now, @now)
    `);
    const now = new Date().toISOString();
    insert.run({
      id: crypto.randomUUID(), name: 'Koçum Benim', slug: 'kocum-benim',
      iosBundleId: 'com.triworkster.kocumbenimmobileapp',
      androidPackage: 'com.triworkster.kocumbenimmobileapp', appStoreUrl: null,
      playStoreUrl: 'https://play.google.com/store/apps/details?id=com.triworkster.kocumbenimmobileapp',
      color: '#f97316', status: 'development', now,
    });
    insert.run({
      id: crypto.randomUUID(), name: 'Trinkow', slug: 'trinkow', iosBundleId: null,
      androidPackage: null, appStoreUrl: null, playStoreUrl: null,
      color: '#7c3aed', status: 'development', now,
    });
  }

  list(): ManagedApp[] {
    return this.db.prepare(`SELECT id, name, slug, ios_bundle_id AS iosBundleId,
      android_package AS androidPackage, app_store_url AS appStoreUrl,
      play_store_url AS playStoreUrl, asobeast_app_id AS asoBeastAppId,
      color, status, created_at AS createdAt, updated_at AS updatedAt
      FROM managed_apps ORDER BY created_at`).all() as ManagedApp[];
  }

  find(id: string): ManagedApp | undefined {
    return this.list().find((app) => app.id === id);
  }

  create(input: Omit<ManagedApp, 'id' | 'createdAt' | 'updatedAt'>): ManagedApp {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    this.db.prepare(`INSERT INTO managed_apps
      (id,name,slug,ios_bundle_id,android_package,app_store_url,play_store_url,asobeast_app_id,color,status,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).run(id, input.name, input.slug, input.iosBundleId,
      input.androidPackage, input.appStoreUrl, input.playStoreUrl, input.asoBeastAppId,
      input.color, input.status, now, now);
    return this.find(id)!;
  }

  update(id: string, input: Partial<Omit<ManagedApp, 'id' | 'createdAt' | 'updatedAt'>>): ManagedApp | undefined {
    const current = this.find(id);
    if (!current) return undefined;
    const next = { ...current, ...input, updatedAt: new Date().toISOString() };
    this.db.prepare(`UPDATE managed_apps SET name=?,slug=?,ios_bundle_id=?,android_package=?,
      app_store_url=?,play_store_url=?,asobeast_app_id=?,color=?,status=?,updated_at=? WHERE id=?`)
      .run(next.name, next.slug, next.iosBundleId, next.androidPackage, next.appStoreUrl,
        next.playStoreUrl, next.asoBeastAppId, next.color, next.status, next.updatedAt, id);
    return this.find(id);
  }
}
