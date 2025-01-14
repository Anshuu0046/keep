"""Fix broken links between alerts and incidents

Revision ID: 991b30bcf0b9
Revises: 89b4d3905d26
Create Date: 2024-10-29 18:37:28.668473

"""

import sqlalchemy as sa
from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "991b30bcf0b9"
down_revision = "89b4d3905d26"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

def upgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name == 'sqlite':
        logger.info("""Migration 83c1020be97d corrupted alert_to_incident.deleted_at at SQLite databases 
because server_default was set to \"1000-01-01 00:00:00\", not \"1000-01-01 00:00:00.000000\". 
Fixing the value in this migration.""")
        
        # Filtering only by deleted_at = '1000-01-01 00:00:00'. If deleted_at is different, it should be already formated well.
        result = connection.execute(sa.text("SELECT incident_id, alert_id, deleted_at FROM alerttoincident WHERE deleted_at = '1000-01-01 00:00:00'"))
        db_datetime_format = "%Y-%m-%d %H:%M:%S.%f"
        print(f"Database datetime format: {db_datetime_format}")
        for row in result:
            try:
                connection.execute(
                    sa.text(
                        "UPDATE alerttoincident SET deleted_at = '1000-01-01 00:00:00.000000' WHERE incident_id = :incident_id AND alert_id = :alert_id AND deleted_at = '1000-01-01 00:00:00'"
                    ),
                    {"incident_id": row["incident_id"], "alert_id": row["alert_id"]}
                )
                print(f"Updated deleted_at for incident_id: {row['incident_id']}, alert_id: {row['alert_id']}")
            except sa.exc.IntegrityError as e:
                if "UNIQUE constraint failed: alerttoincident.alert_id, alerttoincident.incident_id, alerttoincident.deleted_at" in str(e):
                    connection.execute(
                        sa.text(
                            "DELETE FROM alerttoincident WHERE incident_id = :incident_id AND alert_id = :alert_id AND deleted_at = '1000-01-01 00:00:00'"
                        ),
                        {"incident_id": row["incident_id"], "alert_id": row["alert_id"]}
                    )
                    logger.warning(f"IntegrityError encountered for incident_id: {row['incident_id']}, alert_id: {row['alert_id']}. It's a duplicate. Deleted.")
                else:
                    raise e
    else:
        logger.info("Skipping the fix since it's not SQLite.")

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
