CREATE TABLE engineers (
        eid VARCHAR NOT NULL,
        exact_id VARCHAR,
        fte FLOAT,
        start INTEGER,
        "end" INTEGER,
        coordinator VARCHAR, comments unicode, active boolean default 1,
        PRIMARY KEY (eid),
        FOREIGN KEY(coordinator) REFERENCES engineers (eid)
);
CREATE TABLE projects (
        pid VARCHAR NOT NULL,
        exact_code VARCHAR,
        fte FLOAT,
        start INTEGER,
        "end" INTEGER,
        coordinator VARCHAR, comments unicode, active boolean default 1,
        PRIMARY KEY (pid),
        FOREIGN KEY(coordinator) REFERENCES engineers (eid)
);
CREATE TABLE assignments (
        aid INTEGER NOT NULL,
        fte FLOAT,
        eid VARCHAR,
        pid VARCHAR,
        start INTEGER,
        "end" INTEGER,
        PRIMARY KEY (aid),
        FOREIGN KEY(eid) REFERENCES engineers (eid),
        FOREIGN KEY(pid) REFERENCES projects (pid)
);
CREATE TABLE hours(
"Day" INTEGER,
"Month" INTEGER,
"Year" INTEGER,
"Project" TEXT,
"Projectcode" TEXT,
"Medewerker" TEXT,
"Medewerker ID" INTEGER,
"Aantal" INTEGER
);
CREATE TABLE AUDIT(
date VARCHAR,
comment VARCHAR,
aid INTEGER,
oldfte FLOAT,
oldeid VARCHAR,
oldpid VARCHAR,
oldstart INTEGER,
oldend INTEGER,

newfte FLOAT,
neweid VARCHAR,
newpid VARCHAR,
newstart INTEGER,
newend INTEGER,
FOREIGN KEY(aid) REFERENCES assignments(aid),
FOREIGN KEY(oldpid) REFERENCES projects(pid),
FOREIGN KEY(newpid) REFERENCES projects(pid),
                                                               FOREIGN KEY(oldeid) REFERENCES engineers(eid),
FOREIGN KEY(neweid) REFERENCES engineers(eid)
);
CREATE TRIGGER assignmentnew AFTER INSERT ON assignments FOR EACH ROW
BEGIN
INSERT INTO AUDIT
(date, comment, aid, newfte, neweid, newpid, newstart, newend)
VALUES
(datetime(), 'INSERT', new.aid, new.fte, new.eid, new.pid, new.start, new.end);
END;
CREATE TRIGGER assignmentdelete BEFORE DELETE ON assignments
BEGIN
INSERT INTO AUDIT(date, comment, aid, oldfte, oldeid, oldpid, oldstart, oldend)
VALUES
(datetime(), 'DELETE', old.aid, old.fte, old.eid, old.pid, old.start, old.end);
END;
CREATE TRIGGER assignmentupdate AFTER UPDATE ON assignments WHEN
(old.fte <> new.fte OR old.eid <> new.eid OR old.pid <> new.pid OR old.start <> new.start OR old.end <> new.end)
BEGIN
INSERT INTO AUDIT(date, comment, aid, oldfte, oldeid, oldpid, oldstart, oldend, newfte, neweid, newpid, newstart, newend)
VALUES
(datetime(), 'UPDATE', old.aid, old.fte, old.eid, old.pid, old.start, old.end, new.fte, new.eid, new.pid, new.start, new.end);
END;
