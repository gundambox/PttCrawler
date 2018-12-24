"""create initial table

Revision ID: 77eaebfa8062
Revises: 
Create Date: 2018-12-24 15:29:31.660830

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '77eaebfa8062'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('board',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('name',
                              sa.String(length=64),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('ip_asn',
                    sa.Column('ip',
                              sa.String(length=40),
                              nullable=False),
                    sa.Column('asn',
                              sa.String(length=256),
                              nullable=True),
                    sa.Column('asn_date',
                              sa.DateTime(),
                              nullable=True),
                    sa.Column('asn_registry',
                              sa.String(length=256),
                              nullable=True),
                    sa.Column('asn_cidr',
                              sa.String(length=256),
                              nullable=True),
                    sa.Column('asn_country_code',
                              sa.String(length=4),
                              nullable=True),
                    sa.Column('asn_description',
                              sa.String(length=256),
                              nullable=True),
                    sa.Column('asn_raw', sa.String(),
                              nullable=True),
                    sa.PrimaryKeyConstraint('ip')
                    )
    op.create_table('user',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('username',
                              sa.String(length=32),
                              nullable=False),
                    sa.Column('login_times',
                              sa.Integer(),
                              nullable=True),
                    sa.Column('valid_article_count',
                              sa.Integer(),
                              nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('username')
                    )
    op.create_table('article',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('web_id',
                              sa.String(length=20),
                              nullable=False),
                    sa.Column('user_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('board_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('post_datetime',
                              sa.DateTime(),
                              nullable=False),
                    sa.Column('post_ip',
                              sa.String(length=20),
                              nullable=False),
                    sa.ForeignKeyConstraint(['board_id'],
                                            ['board.id'], ),
                    sa.ForeignKeyConstraint(['user_id'],
                                            ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('user_last_record',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('user_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('last_login_datetime',
                              sa.DateTime(),
                              nullable=False),
                    sa.Column('last_login_ip',
                              sa.String(length=40),
                              nullable=False),
                    sa.Column('created_at',
                              sa.DateTime(),
                              nullable=False),
                    sa.ForeignKeyConstraint(['user_id'],
                                            ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('article_history',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('article_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('title',
                              sa.String(length=64),
                              nullable=False),
                    sa.Column('content',
                              sa.String(),
                              nullable=False),
                    sa.Column('start_at',
                              sa.DateTime(),
                              nullable=False),
                    sa.Column('end_at',
                              sa.DateTime(),
                              nullable=False),
                    sa.ForeignKeyConstraint(['article_id'],
                                            ['article.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('push',
                    sa.Column('id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('article_history_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('floor',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('push_tag',
                              sa.String(length=2),
                              nullable=False),
                    sa.Column('push_user_id',
                              sa.Integer(),
                              nullable=False),
                    sa.Column('push_content',
                              sa.String(
                                  length=128),
                              nullable=False),
                    sa.Column('push_ip',
                              sa.String(length=40),
                              nullable=True),
                    sa.Column('push_datetime',
                              sa.DateTime(),
                              nullable=False),
                    sa.ForeignKeyConstraint(['article_history_id'],
                                            ['article_history.id'], ),
                    sa.ForeignKeyConstraint(['push_user_id'],
                                            ['user.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade():
    op.drop_table('push')
    op.drop_table('article_history')
    op.drop_table('user_last_record')
    op.drop_table('article')
    op.drop_table('user')
    op.drop_table('ip_asn')
    op.drop_table('board')
