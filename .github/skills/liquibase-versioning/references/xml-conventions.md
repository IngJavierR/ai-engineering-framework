
# Liquibase XML Conventions

## Format

All structural database changes MUST use XML.

Prefer native Liquibase change types.

SQL may be embedded in XML changesets only when
native change types are insufficient.

## Changelog Layout

Recommended structure for new projects:

src/main/resources/db/changelog/
  db.changelog-master.xml
  changes/
    001-create-customers.xml
    002-add-customer-rfc.xml

Existing projects must preserve their current
approved changelog structure.

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
3. Existing changeset integrity.
4. Application against a disposable database.
5. Resulting schema.
6. Repeat execution.
7. Rollback safety, where applicable.
```
