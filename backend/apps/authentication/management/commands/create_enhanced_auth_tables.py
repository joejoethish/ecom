"""
Management command to create enhanced authentication tables manually.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create enhanced authentication tables manually'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Add new fields to User table
            try:
                cursor.execute("""
                    ALTER TABLE auth_user 
                    ADD COLUMN last_login_ip VARCHAR(45),
                    ADD COLUMN failed_login_attempts INT DEFAULT 0,
                    ADD COLUMN account_locked_until DATETIME NULL,
                    ADD COLUMN password_changed_at DATETIME NULL
                """)
                self.stdout.write(self.style.SUCCESS('Added new fields to User table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'User table fields may already exist: {e}'))

            # Update phone_number field length
            try:
                cursor.execute("""
                    ALTER TABLE auth_user 
                    MODIFY COLUMN phone_number VARCHAR(20)
                """)
                self.stdout.write(self.style.SUCCESS('Updated phone_number field length'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Phone number field update failed: {e}'))

            # Create EmailVerification table
            try:
                cursor.execute("""
                    CREATE TABLE authentication_emailverification (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        created_at DATETIME(6) NOT NULL,
                        updated_at DATETIME(6) NOT NULL,
                        token VARCHAR(64) UNIQUE NOT NULL,
                        expires_at DATETIME(6) NOT NULL,
                        is_used BOOLEAN DEFAULT FALSE,
                        ip_address VARCHAR(45),
                        user_id BIGINT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
                        INDEX idx_token (token),
                        INDEX idx_expires_at (expires_at),
                        INDEX idx_user_is_used (user_id, is_used),
                        INDEX idx_created_at (created_at)
                    )
                """)
                self.stdout.write(self.style.SUCCESS('Created EmailVerification table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'EmailVerification table may already exist: {e}'))

            # Create EmailVerificationAttempt table
            try:
                cursor.execute("""
                    CREATE TABLE authentication_emailverificationattempt (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        created_at DATETIME(6) NOT NULL,
                        updated_at DATETIME(6) NOT NULL,
                        ip_address VARCHAR(45) NOT NULL,
                        email VARCHAR(254) NOT NULL,
                        success BOOLEAN DEFAULT FALSE,
                        user_agent TEXT,
                        INDEX idx_ip_created (ip_address, created_at),
                        INDEX idx_email_created (email, created_at),
                        INDEX idx_created_at (created_at)
                    )
                """)
                self.stdout.write(self.style.SUCCESS('Created EmailVerificationAttempt table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'EmailVerificationAttempt table may already exist: {e}'))

            # Update UserSession table
            try:
                cursor.execute("""
                    ALTER TABLE authentication_usersession 
                    DROP COLUMN device_type,
                    ADD COLUMN device_info JSON,
                    ADD COLUMN login_method VARCHAR(20) DEFAULT 'password',
                    MODIFY COLUMN session_key VARCHAR(128)
                """)
                self.stdout.write(self.style.SUCCESS('Updated UserSession table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'UserSession table update failed: {e}'))

            # Rename PasswordResetToken table and update fields
            try:
                cursor.execute("""
                    ALTER TABLE authentication_passwordresettoken 
                    RENAME TO authentication_passwordreset
                """)
                self.stdout.write(self.style.SUCCESS('Renamed PasswordResetToken table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Table rename failed: {e}'))

            try:
                cursor.execute("""
                    ALTER TABLE authentication_passwordreset 
                    DROP COLUMN token_hash,
                    ADD COLUMN token VARCHAR(64) UNIQUE NOT NULL,
                    ADD COLUMN user_agent TEXT
                """)
                self.stdout.write(self.style.SUCCESS('Updated PasswordReset table fields'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'PasswordReset table update failed: {e}'))

            # Add indexes to User table
            try:
                cursor.execute("""
                    ALTER TABLE auth_user 
                    ADD INDEX idx_is_email_verified (is_email_verified),
                    ADD INDEX idx_last_login_ip (last_login_ip),
                    ADD INDEX idx_account_locked_until (account_locked_until)
                """)
                self.stdout.write(self.style.SUCCESS('Added indexes to User table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'User table indexes may already exist: {e}'))

            # Add indexes to UserSession table
            try:
                cursor.execute("""
                    ALTER TABLE authentication_usersession 
                    ADD INDEX idx_last_activity (last_activity),
                    ADD INDEX idx_ip_address (ip_address)
                """)
                self.stdout.write(self.style.SUCCESS('Added indexes to UserSession table'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'UserSession table indexes may already exist: {e}'))

        self.stdout.write(self.style.SUCCESS('Enhanced authentication tables setup completed'))