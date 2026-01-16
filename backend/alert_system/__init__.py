"""
Alert System Module

Provides unified alerting capabilities through multiple channels:
- Email (SMTP)
- Slack webhooks
- Discord webhooks
- Custom webhooks
"""

from .alert_manager import AlertManager, AlertConfig, AlertResult, alert_manager
from .email_alerts import EmailAlertSystem
from .webhook_alerts import WebhookAlertSystem

__all__ = [
    'AlertManager',
    'AlertConfig', 
    'AlertResult',
    'alert_manager',
    'EmailAlertSystem',
    'WebhookAlertSystem'
]
