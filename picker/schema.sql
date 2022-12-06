DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS collections;
DROP TABLE IF EXISTS records;
DROP TABLE IF EXISTS media;
DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS recordmedia;
DROP TABLE IF EXISTS recordpeople;
DROP TABLE IF EXISTS recordloaded;
DROP TABLE IF EXISTS projectrecords;
DROP TABLE IF EXISTS projectmedia;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "user",
    active TEXT NOT NULL DEFAULT "y",
    currentProject INTEGER
);

CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    facetedTitle TEXT NOT NULL,
    lastHarvested TEXT,
    objectType TEXT NOT NULL
);

CREATE TABLE records (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recordCreated TEXT NOT NULL DEFAULT "1970-01-01T23:59:59Z",
    recordModified TEXT NOT NULL DEFAULT "1970-01-01T23:59:59Z",
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    collectionId INTEGER NOT NULL,
    identifier TEXT NOT NULL,
    dateLabel TEXT NOT NULL,
    dateValue TEXT NOT NULL,
    personLabel TEXT NOT NULL,
    qualityScore REAL NOT NULL
);

CREATE TABLE media (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    license TEXT NOT NULL
);

CREATE TABLE people (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    facetedTitle TEXT NOT NULL,
    baseUrl TEXT NOT NULL
);

CREATE TABLE recordmedia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recordId INTEGER,
    mediaId INTEGER,
    FOREIGN KEY(recordId) REFERENCES records(irn),
    FOREIGN KEY(mediaId) REFERENCES media(irn)
);

CREATE TABLE recordpeople (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recordId INTEGER,
    personId INTEGER,
    FOREIGN KEY(recordId) REFERENCES records(irn),
    FOREIGN KEY(personId) REFERENCES people(irn)
);

CREATE TABLE recordloaded (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recordId INTEGER,
    url TEXT,
    FOREIGN KEY(recordId) REFERENCES records(irn)
);

CREATE TABLE projectrecords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projectId INTEGER,
    recordId INTEGER,
    include TEXT,
    complete TEXT,
    loaded TEXT,
    FOREIGN KEY(projectId) REFERENCES project(id),
    FOREIGN KEY(recordId) REFERENCES records(irn)
);

CREATE TABLE projectmedia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projectId INTEGER,
    mediaId INTEGER,
    include TEXT,
    FOREIGN KEY(projectId) REFERENCES project(id),
    FOREIGN KEY(mediaId) REFERENCES media(irn)
);