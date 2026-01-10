"""Initial schema for TALANTA AI

Revision ID: 001_initial
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('maisha_namba_hash', sa.String(64), unique=True, nullable=True, index=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('location_lat', sa.Float, nullable=True),
        sa.Column('location_long', sa.Float, nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),
        sa.Column('trust_score', sa.Integer, default=0),
        sa.Column('role', sa.String(20), default='CITIZEN', nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('last_active_at', sa.DateTime),
    )
    
    # Create verifications table
    op.create_table(
        'verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('s3_url', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('ocr_data', postgresql.JSONB, nullable=True),
        sa.Column('extracted_name', sa.String(255), nullable=True),
        sa.Column('extracted_serial', sa.String(100), nullable=True),
        sa.Column('extracted_skill', sa.String(255), nullable=True),
        sa.Column('extracted_institution', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='PENDING', nullable=False, index=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('trust_score_delta', sa.Integer, default=0),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verified_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False, index=True),
        sa.Column('old_value', postgresql.JSONB, nullable=True),
        sa.Column('new_value', postgresql.JSONB, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
    )
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('required_skills', postgresql.JSONB, nullable=False),
        sa.Column('experience_years', sa.Integer, nullable=True),
        sa.Column('education_level', sa.String(100), nullable=True),
        sa.Column('salary_min', sa.Integer, nullable=True),
        sa.Column('salary_max', sa.Integer, nullable=True),
        sa.Column('currency', sa.String(3), default='KES'),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('location_lat', sa.Float, nullable=True),
        sa.Column('location_long', sa.Float, nullable=True),
        sa.Column('is_remote', sa.String(20), default='NO'),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('source_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.String(20), default='ACTIVE'),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('scraped_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    # Create training_centers table
    op.create_table(
        'training_centers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('accreditation', sa.String(100), nullable=True),
        sa.Column('courses', postgresql.JSONB, nullable=False),
        sa.Column('location_name', sa.String(255), nullable=False),
        sa.Column('location_lat', sa.Float, nullable=False),
        sa.Column('location_long', sa.Float, nullable=False),
        sa.Column('county', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(512), nullable=True),
        sa.Column('is_active', sa.String(20), default='ACTIVE'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    
    # Create indexes
    op.create_index('idx_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_job_location', 'jobs', ['location'])


def downgrade() -> None:
    op.drop_table('training_centers')
    op.drop_table('jobs')
    op.drop_table('audit_logs')
    op.drop_table('verifications')
    op.drop_table('users')
