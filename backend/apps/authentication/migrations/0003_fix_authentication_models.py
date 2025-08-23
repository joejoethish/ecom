# Generated manually to fix authentication models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_enhanced_authentication_models"),
    ]

    operations = [
        # Update PasswordReset model options
        migrations.AlterModelOptions(
            name="passwordreset",
            options={
                "verbose_name": "Password Reset",
                "verbose_name_plural": "Password Resets",
            },
        ),
        
        # Update PasswordReset foreign key
        migrations.AlterField(
            model_name="passwordreset",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="password_resets",
                to="authentication.user",
            ),
        ),
        
        # Create UserProfile model
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('alternate_phone', models.CharField(blank=True, max_length=15)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=100)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=15)),
                ('preferences', models.JSONField(blank=True, default=dict)),
                ('facebook_url', models.URLField(blank=True)),
                ('twitter_url', models.URLField(blank=True)),
                ('instagram_url', models.URLField(blank=True)),
                ('linkedin_url', models.URLField(blank=True)),
                ('profile_visibility', models.CharField(
                    choices=[
                        ('public', 'Public'),
                        ('private', 'Private'),
                        ('friends', 'Friends Only'),
                    ],
                    default='public',
                    max_length=20
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='authentication.user'
                )),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        
        # Create PasswordResetAttempt model
        migrations.CreateModel(
            name='PasswordResetAttempt',
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
                'verbose_name': 'Password Reset Attempt',
                'verbose_name_plural': 'Password Reset Attempts',
            },
        ),
        
        # Add indexes for PasswordResetAttempt
        migrations.AddIndex(
            model_name="passwordresetattempt",
            index=models.Index(fields=["ip_address", "created_at"], name="authenticat_ip_addr_02c1c5_idx"),
        ),
        migrations.AddIndex(
            model_name="passwordresetattempt",
            index=models.Index(fields=["email", "created_at"], name="authenticat_email_6aad5c_idx"),
        ),
        migrations.AddIndex(
            model_name="passwordresetattempt",
            index=models.Index(fields=["created_at"], name="authenticat_created_d8a3f2_idx"),
        ),
        migrations.AddIndex(
            model_name="passwordresetattempt",
            index=models.Index(fields=["ip_address", "success"], name="authenticat_ip_addr_success_idx"),
        ),
    ]