# Generated manually for enhanced authentication models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_add_password_reset_models'),
    ]

    operations = [
        # Add new fields to User model
        migrations.AddField(
            model_name='user',
            name='last_login_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='failed_login_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='account_locked_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='password_changed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Update phone_number field to allow longer numbers
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(
                blank=True, 
                max_length=20, 
                null=True, 
                validators=[django.core.validators.RegexValidator(
                    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", 
                    regex='^\\+?1?\\d{9,15}$'
                )]
            ),
        ),
        
        # Add super_admin to user_type choices
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(
                choices=[
                    ('customer', 'Customer'), 
                    ('seller', 'Seller'), 
                    ('admin', 'Admin'), 
                    ('super_admin', 'Super Admin')
                ], 
                default='customer', 
                max_length=20
            ),
        ),
        
        # Create EmailVerification model
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('token', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_verifications', to='authentication.user')),
            ],
            options={
                'verbose_name': 'Email Verification',
                'verbose_name_plural': 'Email Verifications',
            },
        ),
        
        # Create EmailVerificationAttempt model
        migrations.CreateModel(
            name='EmailVerificationAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ip_address', models.GenericIPAddressField()),
                ('email', models.EmailField(max_length=254)),
                ('success', models.BooleanField(default=False)),
                ('user_agent', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Email Verification Attempt',
                'verbose_name_plural': 'Email Verification Attempts',
            },
        ),
        
        # Update UserSession model
        migrations.RemoveField(
            model_name='usersession',
            name='device_type',
        ),
        migrations.AddField(
            model_name='usersession',
            name='device_info',
            field=models.JSONField(default=dict, help_text='Device information including browser, OS, device type'),
        ),
        migrations.AddField(
            model_name='usersession',
            name='login_method',
            field=models.CharField(
                choices=[
                    ('password', 'Password'), 
                    ('social', 'Social Login'), 
                    ('admin', 'Admin Login')
                ], 
                default='password', 
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='usersession',
            name='session_key',
            field=models.CharField(max_length=128, unique=True),
        ),
        
        # Rename PasswordResetToken to PasswordReset and update fields
        migrations.RenameModel(
            old_name='PasswordResetToken',
            new_name='PasswordReset',
        ),
        migrations.RemoveField(
            model_name='passwordreset',
            name='token_hash',
        ),
        migrations.AddField(
            model_name='passwordreset',
            name='token',
            field=models.CharField(max_length=64, unique=True, default='temp'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='passwordreset',
            name='user_agent',
            field=models.TextField(blank=True),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_email_verified'], name='auth_user_is_emai_c40f2e_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['last_login_ip'], name='auth_user_last_lo_936cfe_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['account_locked_until'], name='auth_user_account_467b49_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverification',
            index=models.Index(fields=['token'], name='authenticat_token_499884_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverification',
            index=models.Index(fields=['expires_at'], name='authenticat_expires_8662be_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverification',
            index=models.Index(fields=['user', 'is_used'], name='authenticat_user_id_9751b1_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverification',
            index=models.Index(fields=['created_at'], name='authenticat_created_10b06c_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverificationattempt',
            index=models.Index(fields=['ip_address', 'created_at'], name='authenticat_ip_addr_936cfe_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverificationattempt',
            index=models.Index(fields=['email', 'created_at'], name='authenticat_email_467b49_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverificationattempt',
            index=models.Index(fields=['created_at'], name='authenticat_created_5ccc6c_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['last_activity'], name='authenticat_last_ac_f427c8_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['ip_address'], name='authenticat_ip_addr_1fea71_idx'),
        ),
    ]