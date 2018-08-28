"""
SQL Queries for RAVI.
"""

from sqlalchemy import text

PROJECT_AND_FTES = text("""
SELECT
  *
FROM (
    SELECT
        pid,
        fte,
        start,
        end,
        coordinator,
        comments,
        exact_code,
        active
    FROM
        projects
    ORDER BY
        pid
) LEFT OUTER JOIN (
    SELECT
        pid,
        SUM(assignments.fte * (assignments.end - assignments.start)) / 12 AS assigned
    FROM
        assignments
    GROUP BY
        pid
) USING (
    pid
)
"""
)

REQUIRED_FTE=text("""
WITH boundaries AS (
    SELECT
        start AS 'edge'
    FROM
        projects
    UNION SELECT
        end AS 'edge' FROM projects
    ORDER BY edge
),

intervals AS (
    SELECT
        b1.edge AS start,
        b2.edge AS end
    FROM
        boundaries b1
    JOIN
        boundaries b2
    ON b2.edge = (
        SELECT
            MIN(edge)
        FROM
            boundaries b3
        WHERE
            b3.edge > b1.edge
    )
)

SELECT
    intervals.start AS start,
    intervals.end AS end,
    SUM(projects.fte * 12 / (projects.end - projects.start)) AS fte,
    intervals.end - intervals.start AS months
FROM
    projects,
    intervals
WHERE
    projects.start < intervals.end
    AND projects.end > intervals.start
GROUP BY
    intervals.start,
    intervals.end
"""
)

AVAILABLE_FTE=text("""
WITH boundaries AS (
    SELECT
        start AS 'edge'
    FROM
        assignments
    WHERE
        assignments.eid NOT LIKE '00_%'
    UNION SELECT
        end AS 'edge'
    FROM
        assignments
    WHERE
        assignments.eid NOT LIKE '00_%'
    ORDER BY
        edge
),

intervals AS (
    SELECT
        b1.edge AS start,
        b2.edge AS end
    FROM 
        boundaries b1
    JOIN
        boundaries b2
    ON
        b2.edge = (
            SELECT
                MIN(edge)
            FROM
                boundaries b3
            WHERE
                b3.edge > b1.edge
        )
)

SELECT
    intervals.start AS start,
    intervals.end AS end,
    SUM(assignments.fte) AS fte,
    intervals.end - intervals.start AS months
FROM
    assignments,
    intervals
WHERE
    assignments.start < intervals.end
    AND assignments.end > intervals.start
    AND assignments.eid NOT LIKE '00_%'
GROUP BY
    intervals.start,
    intervals.end
ORDER BY
    intervals.start
"""
)

ENGINEER_LOAD = text("""
WITH boundaries AS (
    SELECT
        eid,
        end AS 'edge'
    FROM
        assignments
    UNION SELECT
        eid,
        start AS 'edge'
    FROM
        assignments
    UNION SELECT
        eid,
        start AS 'edge'
    FROM engineers
    UNION SELECT
        eid,
        end AS 'edge'
    FROM
        engineers
    ORDER BY
        eid,
        edge
),

intervals AS (
    SELECT
        b1.eid AS eid,
        b1.edge AS start,
        b2.edge AS end
    FROM
        boundaries b1
    JOIN
        boundaries b2
    ON
        b1.eid = b2.eid
        AND b2.edge = (
            SELECT
                MIN(edge)
            FROM
                boundaries b3
            WHERE
                b3.edge > b1.edge
                AND b3.eid = b2.eid
        )
),

load AS (
    SELECT
        intervals.eid AS eid,
        intervals.start AS start,
        intervals.end AS end,
        SUM(assignments.fte) AS fte
    FROM
        assignments,
        intervals
    WHERE
        assignments.eid = intervals.eid
        AND assignments.start < intervals.end
        AND assignments.end > intervals.start
    GROUP BY
        intervals.eid,
        intervals.start,
        intervals.end
)

SELECT
    load.eid AS eid,
    load.start AS start,
    load.end AS end,
    load.fte - engineers.fte AS fte
FROM
    load,
    engineers
WHERE
    load.eid = engineers.eid
"""
)

ENGINEERS= text("""
SELECT
    *
FROM (
    SELECT
        engineers.eid AS eid,
        engineers.start AS start,
        engineers.end AS end,
        engineers.fte AS fte,
        engineers.exact_id AS exact_id,
        engineers.coordinator AS coordinator,
        engineers.comments AS comments,
        engineers.active AS active
    FROM
        engineers
    ORDER BY
        engineers.eid
) LEFT OUTER JOIN (
    WITH edges AS (
        SELECT
            (strftime('%Y', date('now')) * 12 + strftime('%m', date('now')) - 1) AS start,
            (strftime('%Y', date('now')) * 12 + strftime('%m', date('now')) - 1 + 3) AS end
    )
    SELECT
        engineers.eid AS eid,
        SUM(
            MIN(
                MAX(
                    assignments.end - edges.start,
                    edges.end - assignments.start,
                    0
                ),
                assignments.end - assignments.start,
                edges.end - edges.start
            ) * assignments.fte
        ) / 3 AS assigned,
        engineers.fte AS available
    FROM
        edges,
        assignments,
        engineers
    WHERE
        edges.start < assignments.end
        AND edges.end > assignments.start
        AND assignments.eid = engineers.eid
    GROUP BY
        engineers.eid
) USING (
    eid
)
"""
)

PROJECT_WRITTEN_HOURS=text("""
SELECT
    Medewerker,
    SUM(Aantal) AS Aantal,
    Year,
    Month
FROM
    hours
WHERE
    Projectcode = :Projectcode
GROUP BY
    Medewerker,
    Year,
    Month
ORDER BY
    Year,
    Month,
    Medewerker
"""
)

GET_LOG=text("""
SELECT
    *
FROM
    AUDIT
WHERE 
    (
        'all' = :engineer
        OR oldpid = :engineer
        OR newpid = :engineer
    ) AND (
        'all' = :project
        OR oldeid = :project
        OR neweid = :project
    )
ORDER BY
    date
DESC LIMIT 25
"""
)

GET_ASSIGNMENTS=text("""
SELECT
    aid,
    pid,
    eid,
    start,
    end,
    fte
FROM
    assignments 
WHERE
    (
        'all' = :pid
        OR pid = :pid
    ) AND (
        'all' = :eid
        OR eid = :eid
    )
ORDER BY
    pid,
    eid,
    start
""")
