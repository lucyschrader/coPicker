DROP TABLE IF EXISTS collections;
DROP TABLE IF EXISTS records;
DROP TABLE IF EXISTS media;
DROP TABLE IF EXISTS people;
DROP TABLE IF EXISTS recordmedia;
DROP TABLE IF EXISTS recordpeople;

CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    facetedTitle TEXT NOT NULL,
    lastHarvested TIMESTAMP,
    totalImages INTEGER,
    loadedImages INTEGER,
    includedImages INTEGER,
    excludedImages INTEGER,
    objectType TEXT NOT NULL
);

CREATE TABLE records (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    collectionId INTEGER NOT NULL,
    identifier TEXT NOT NULL,
    dateLabel TEXT NOT NULL,
    dateValue TEXT NOT NULL,
    personLabel TEXT NOT NULL,
    qualityScore REAL NOT NULL,
    include TEXT
);

CREATE TABLE media (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    license TEXT NOT NULL,
    include TEXT
);

CREATE TABLE people (
    irn INTEGER PRIMARY KEY NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL
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
)