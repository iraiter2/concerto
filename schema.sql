BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "songs" (
	"id"	INTEGER,
	"artist"	TEXT,
	"genre"	TEXT,
	"year"	INTEGER,
	"album"	TEXT,
	"name"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "concerts" (
	"id"	INTEGER,
	"genre"	TEXT,
	"time"	INTEGER,
	"name"	TEXT,
	"location"	TEXT,
	"venue"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "concert_artists" (
	"artist"	TEXT,
	"concert"	INTEGER,
	FOREIGN KEY("concert") REFERENCES "concerts"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "chat_messages" (
	"carpool_id"	INTEGER,
	"user_id"	INTEGER,
	"content"	TEXT,
	"time"	INTEGER,
	FOREIGN KEY("carpool_id") REFERENCES "carpools"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "carpool_members" (
	"carpool_id"	INTEGER,
	"member_id"	INTEGER,
	FOREIGN KEY("member_id") REFERENCES "users"("id") ON DELETE CASCADE,
	FOREIGN KEY("carpool_id") REFERENCES "carpools"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "carpools" (
	"id"	INTEGER,
	"arrival_time"	TEXT,
	"driver_id"	INTEGER,
	"car_description"	TEXT,
	"concert"	INTEGER,
	FOREIGN KEY("concert") REFERENCES "concerts"("id") ON DELETE CASCADE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"salt"	TEXT NOT NULL,
	"displayname"	TEXT NOT NULL,
	"permissions"	INTEGER NOT NULL DEFAULT 0,
	"profile_description"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
COMMIT;
