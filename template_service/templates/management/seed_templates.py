from django.core.management.base import BaseCommand
from templates.models import EmailTemplate


class Command(BaseCommand):
    help = 'Seed database with sample email templates'
    
    def handle(self, *args, **kwargs):
        templates = [
            {
                'name': 'welcome_email',
                'template_type': 'welcome',
                'subject': 'Welcome to {{app_name}}, {{user.name}}!',
                'html_content': '''
                    <html>
                    <body>
                        <h1>Welcome {{user.name}}!</h1>
                        <p>We're excited to have you join {{app_name}}.</p>
                        <p>Your email is: {{user.email}}</p>
                        <p>Get started by exploring our features.</p>
                        <a href="{{dashboard_url}}">Go to Dashboard</a>
                    </body>
                    </html>
                ''',
                'text_content': 'Welcome {{user.name}}! We\'re excited to have you.',
                'description': 'Welcome email sent to new users',
                'required_variables': ['user.name', 'user.email', 'app_name', 'dashboard_url'],
            },
            {
                'name': 'reset_password',
                'template_type': 'reset_password',
                'subject': 'Reset Your Password - {{app_name}}',
                'html_content': '''
                    <html>
                    <body>
                        <h2>Password Reset Request</h2>
                        <p>Hi {{user.name}},</p>
                        <p>We received a request to reset your password.</p>
                        <p>Click the link below to reset your password:</p>
                        <a href="{{reset_url}}">Reset Password</a>
                        <p>This link expires in {{expiry_hours}} hours.</p>
                        <p>If you didn't request this, please ignore this email.</p>
                    </body>
                    </html>
                ''',
                'text_content': 'Password reset link: {{reset_url}}',
                'description': 'Password reset email',
                'required_variables': ['user.name', 'reset_url', 'expiry_hours', 'app_name'],
            },
            {
                'name': 'order_confirmation',
                'template_type': 'transactional',
                'subject': 'Order Confirmation #{{order.id}}',
                'html_content': '''
                    <html>
                    <body>
                        <h1>Order Confirmation</h1>
                        <p>Hi {{user.name}},</p>
                        <p>Thank you for your order!</p>
                        <h3>Order Details:</h3>
                        <p>Order ID: {{order.id}}</p>
                        <p>Total: ${{order.total}}</p>
                        <p>Status: {{order.status}}</p>
                        <p>Estimated delivery: {{delivery_date}}</p>
                    </body>
                    </html>
                ''',
                'text_content': 'Order #{{order.id}} confirmed. Total: ${{order.total}}',
                'description': 'Order confirmation email',
                'required_variables': ['user.name', 'order.id', 'order.total', 'order.status', 'delivery_date'],
            },
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created template: {template.name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Template already exists: {template.name}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully seeded {created_count} templates")
        )
