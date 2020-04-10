BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"salt"	TEXT NOT NULL,
	"displayname"	TEXT NOT NULL,
	"invite"	TEXT,
	"permissions"	INTEGER NOT NULL DEFAULT 0,
	"profile_description"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "invite" (
	"code"	TEXT NOT NULL UNIQUE,
	"owner"	INTEGER NOT NULL,
	"permissions"	INTEGER NOT NULL,
	PRIMARY KEY("code"),
	FOREIGN KEY("owner") REFERENCES "users"("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "songs" (
	"id"	INTEGER,
	"artist"	TEXT,
	"genre"	TEXT,
	"year"	INTEGER,
	"album"	TEXT,
	"name"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "concerts" (
	"id"	INTEGER,
	"artist"	TEXT,
	"genre"	TEXT,
	"time"	INTEGER,
	"name"	TEXT,
	"location"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "carpools" (
	"id"	INTEGER,
	"arrival_time"	TEXT,
	"driver_id"	INTEGER,
	"car_description"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "chatrooms" (
	"id"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "chat_messages" (
	"chat_id"	INTEGER,
	"user_id"	INTEGER,
	"content"	TEXT,
	"time"	INTEGER
);
INSERT INTO "users" VALUES (0,'','','','',NULL,0,' ');
INSERT INTO "users" VALUES (2,'admin','91750ca5b6fcf87daa43063128d339491263e7eaa4f645a39f58639a7f04c21f','KGCddERfzTI0oTM51uxsDg==','admin','a',2,' ');
INSERT INTO "invite" VALUES ('a',0,2);
COMMIT;
