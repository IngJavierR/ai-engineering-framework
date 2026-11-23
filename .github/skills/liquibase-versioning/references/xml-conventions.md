
# Liquibase XML Conventions

## Format

All structural database changes MUST use XML.

Prefer native Liquibase change types.

SQL may be embedded in XML changesets only when
native change types are insufficient.

## Changelog Layout

Recommended Java structure for new projects:

src/main/resources/db/changelog/
  db.changelog-master.xml
  changes/
    001-create-customers.xml
    002-add-customer-rfc.xml

For non-Java services, use:

<service-root>/db/changelog/
  db.changelog-master.xml
  changes/
    001-create-customers.xml

Existing projects must preserve their current
approved changelog structure.

Execute Java migrations through the approved Maven or Gradle plugin. For other
stacks, use the Liquibase CLI or official `liquibase/liquibase` Docker image,
with the consumer-pinned version recorded in validation evidence. If the
consumer already manages the same schema with Alembic, Flyway, Prisma, EF, or
another migration tool, do not add Liquibase in parallel: report `BLOCKED`
until a migration decision or a client-policy exception is approved.

## PostgreSQL with Docker and Liquibase 5.x

For non-JVM stacks, pin the PostgreSQL and Liquibase images in the consumer.
Liquibase 5.x installs extensions through Liquibase Package Manager (LPM), so
install the PostgreSQL extension in the same ephemeral container invocation:

```bash
docker run --rm --network host \
  -v "$PWD:/workspace" -w /workspace \
  liquibase/liquibase:5.0 \
  sh -c 'lpm add postgresql && liquibase --changelog-file=backend/db/changelog/db.changelog-master.xml validate'
```

Use the consumer-approved network and credentials mechanism instead of putting
credentials in this command. Record the pinned image tag, installed extension,
and PostgreSQL version in validation evidence. Run `update` only against an
authorized disposable or target environment after validation.

## Naming

Use descriptive file names.

Example:
003-add-customer-email-index.xml

Changeset identity:
- id: descriptive and unique within the project
- author: approved project or team identifier
- path: preserve the original changelog path

Remember that Liquibase changeset identity
includes the changelog file path.

Never rename or relocate an applied changeset
without an approved migration strategy.

## Example: Add a Column

The following is an illustrative changeset:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
      http://www.liquibase.org/xml/ns/dbchangelog
      https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="002-add-customer-rfc"
               author="engineering">

        <preConditions onFail="HALT">
            <tableExists tableName="customers"/>
            <not>
                <columnExists
                    tableName="customers"
                    columnName="rfc"/>
            </not>
        </preConditions>

        <addColumn tableName="customers">
            <column name="rfc" type="varchar(13)"/>
        </addColumn>

        <rollback>
            <dropColumn
                tableName="customers"
                columnName="rfc"/>
        </rollback>

    </changeSet>
</databaseChangeLog>
```

## Rollback Warning

The example rollback deletes the new column
and any data subsequently written into it.

Use it only when the resulting data loss
is acceptable and explicitly authorized.

A forward recovery plan may be safer.

## Root Changelog

For a new project, use explicit includes:

```xml
<include
    file="changes/001-create-customers.xml"
    relativeToChangelogFile="true"/>

<include
    file="changes/002-add-customer-rfc.xml"
    relativeToChangelogFile="true"/>
```

These elements belong inside a valid
databaseChangeLog root element.

## Changeset Rules

- Never edit a previously executed changeset.
- Verify immutability using the approved baseline content or hashes
    calculated from that baseline. Never add invented hash values.
- Avoid unnecessary changes within one changeset.
- Preserve deterministic execution ordering.
- Review preconditions before deployment.
- Use compatible syntax for the approved
  Liquibase version and database engine.
- Document platform-specific SQL.
- Avoid destructive schema changes by default.

## Validation

A generated XML document is not automatically
a validated database migration.

Check:
1. XML syntax.
2. Liquibase validation.
3. Existing changeset integrity against a verifiable baseline.
4. Application against a disposable database; for evolutionary
   changes, begin with the previous schema and existing records.
5. Resulting schema.
6. Data preservation.
7. One DATABASECHANGELOG record for each executed changeset.
8. Repeat execution.
9. Index and constraint behavior on the real database engine.
10. Concurrent behavior when a changed rule depends on concurrency,
    such as uniqueness.
11. Rollback safety, where applicable.

## Test Data and Rollback

Loading and cleaning test data are DML activities, not structural DDL;
they may be used to prepare validation scenarios under project policy.

A rollback that drops a column or table can discard data written after
deployment. State this risk and prefer a forward recovery strategy
when retaining that data is required.

## Validation Evidence

Use GENERATED for produced artifacts, COMPILED for evidenced successful
compilation, TESTED for executed checks with known scope, and VALIDATED
only when the declared acceptance criteria have sufficient evidence.
Report NOT_RUN for applicable checks that remain pending.