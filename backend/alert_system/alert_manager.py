"""
Unified Alert Manager

Provides a single interface for sending alerts through multiple channels
(email, webhooks) with configuration from environment variables.
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from dotenv import load_dotenv

from .email_alerts import EmailAlertSystem
from .webhook_alerts import WebhookAlertSystem
from ..anomaly_detection.statistical_methods import AnomalyResult

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuration for alert channels"""
    # Email configuration
    email_enabled: bool = False
    smtp_server: str = ""
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    default_recipients: List[str] = None
    
    # Webhook configuration
    slack_webhook_url: str = ""
    discord_webhook_url: str = ""
    custom_webhook_url: str = ""
    
    # Alert settings
    min_score_threshold: float = 1.5
    batch_alerts: bool = True
    
    def __post_init__(self):
        if self.default_recipients is None:
            self.default_recipients = []
    
    @classmethod
    def from_environment(cls) -> 'AlertConfig':
        """Load configuration from environment variables"""
        return cls(
            email_enabled=os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            sender_email=os.getenv('ALERT_EMAIL_SENDER', ''),
            sender_password=os.getenv('ALERT_EMAIL_PASSWORD', ''),
            default_recipients=os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',') if os.getenv('ALERT_EMAIL_RECIPIENTS') else [],
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
            discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL', ''),
            custom_webhook_url=os.getenv('CUSTOM_WEBHOOK_URL', ''),
            min_score_threshold=float(os.getenv('ALERT_MIN_SCORE', '1.5')),
            batch_alerts=os.getenv('ALERT_BATCH', 'true').lower() == 'true'
        )


class AlertResult:
    """Result of an alert attempt"""
    
    def __init__(self, 
                 channel: str,
                 success: bool,
                 message: str = "",
                 error: Optional[str] = None):
        self.channel = channel
        self.success = success
        self.message = message
        self.error = error
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            'channel': self.channel,
            'success': self.success,
            'message': self.message,
            'error': self.error,
            'timestamp': self.timestamp.isoformat()
        }


class AlertManager:
    """
    Unified manager for sending alerts through multiple channels.
    
    Features:
    - Email alerts via SMTP
    - Slack webhook notifications
    - Discord webhook notifications
    - Custom webhook support
    - Configurable thresholds
    - Batch alert support
    """
    
    def __init__(self, config: Optional[AlertConfig] = None):
        """
        Initialize the alert manager.
        
        Args:
            config: Alert configuration. If None, loads from environment.
        """
        self.config = config or AlertConfig.from_environment()
        
        # Initialize email system if configured
        self.email_system = None
        if self.config.email_enabled and self.config.sender_email:
            try:
                self.email_system = EmailAlertSystem(
                    smtp_server=self.config.smtp_server,
                    smtp_port=self.config.smtp_port,
                    sender_email=self.config.sender_email,
                    sender_password=self.config.sender_password
                )
                logger.info("Email alert system initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize email system: {e}")
        
        # Initialize webhook system
        webhook_urls = {}
        if self.config.slack_webhook_url:
            webhook_urls['slack'] = self.config.slack_webhook_url
        if self.config.discord_webhook_url:
            webhook_urls['discord'] = self.config.discord_webhook_url
        if self.config.custom_webhook_url:
            webhook_urls['custom'] = self.config.custom_webhook_url
        
        self.webhook_system = None
        if webhook_urls:
            self.webhook_system = WebhookAlertSystem(webhook_urls)
            logger.info(f"Webhook alert system initialized with channels: {list(webhook_urls.keys())}")
        
        # Alert history
        self._alert_history: List[AlertResult] = []
    
    def filter_significant_anomalies(self, 
                                     anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """Filter anomalies by score threshold"""
        return [a for a in anomalies if a.score >= self.config.min_score_threshold]
    
    def send_alert(self,
                   symbol: str,
                   anomalies: List[AnomalyResult],
                   recipients: Optional[List[str]] = None,
                   channels: Optional[List[str]] = None) -> List[AlertResult]:
        """
        Send alerts through configured channels.
        
        Args:
            symbol: Stock symbol
            anomalies: List of detected anomalies
            recipients: Optional email recipients (uses default if not provided)
            channels: Optional specific channels (uses all configured if not provided)
            
        Returns:
            List of alert results
        """
        # Filter by threshold
        significant_anomalies = self.filter_significant_anomalies(anomalies)
        
        if not significant_anomalies:
            logger.info(f"No significant anomalies to alert for {symbol}")
            return []
        
        results = []
        
        # Determine which channels to use
        if channels is None:
            channels = []
            if self.email_system:
                channels.append('email')
            if self.webhook_system:
                if self.config.slack_webhook_url:
                    channels.append('slack')
                if self.config.discord_webhook_url:
                    channels.append('discord')
                if self.config.custom_webhook_url:
                    channels.append('custom')
        
        # Send email alerts
        if 'email' in channels and self.email_system:
            email_recipients = recipients or self.config.default_recipients
            for recipient in email_recipients:
                if recipient.strip():
                    try:
                        success = self.email_system.send_alert(
                            recipient=recipient.strip(),
                            symbol=symbol,
                            anomalies=significant_anomalies
                        )
                        result = AlertResult(
                            channel='email',
                            success=success,
                            message=f"Email sent to {recipient}" if success else f"Failed to send to {recipient}"
                        )
                    except Exception as e:
                        result = AlertResult(
                            channel='email',
                            success=False,
                            error=str(e)
                        )
                    results.append(result)
                    self._alert_history.append(result)
        
        # Send webhook alerts
        if self.webhook_system:
            webhook_channels = [c for c in channels if c in ['slack', 'discord', 'custom']]
            if webhook_channels:
                try:
                    webhook_results = self.webhook_system.send_alert(
                        symbol=symbol,
                        anomalies=significant_anomalies
                    )
                    for channel, success in webhook_results.items():
                        result = AlertResult(
                            channel=channel,
                            success=success,
                            message=f"Webhook {channel} {'succeeded' if success else 'failed'}"
                        )
                        results.append(result)
                        self._alert_history.append(result)
                except Exception as e:
                    for channel in webhook_channels:
                        result = AlertResult(
                            channel=channel,
                            success=False,
                            error=str(e)
                        )
                        results.append(result)
                        self._alert_history.append(result)
        
        # Log summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Sent {successful}/{len(results)} alerts for {symbol} ({len(significant_anomalies)} anomalies)")
        
        return results
    
    def send_daily_summary(self,
                           daily_anomalies: Dict[str, List[AnomalyResult]],
                           recipients: Optional[List[str]] = None) -> List[AlertResult]:
        """
        Send a daily summary of all detected anomalies.
        
        Args:
            daily_anomalies: Dictionary of anomalies by symbol
            recipients: Optional email recipients
            
        Returns:
            List of alert results
        """
        # Filter significant anomalies for each symbol
        filtered_anomalies = {}
        for symbol, anomalies in daily_anomalies.items():
            significant = self.filter_significant_anomalies(anomalies)
            if significant:
                filtered_anomalies[symbol] = significant
        
        if not filtered_anomalies:
            logger.info("No significant anomalies for daily summary")
            return []
        
        results = []
        
        # Send email summary
        if self.email_system:
            email_recipients = recipients or self.config.default_recipients
            for recipient in email_recipients:
                if recipient.strip():
                    try:
                        success = self.email_system.send_daily_summary(
                            recipient=recipient.strip(),
                            daily_anomalies=filtered_anomalies
                        )
                        result = AlertResult(
                            channel='email',
                            success=success,
                            message=f"Daily summary sent to {recipient}"
                        )
                    except Exception as e:
                        result = AlertResult(
                            channel='email',
                            success=False,
                            error=str(e)
                        )
                    results.append(result)
                    self._alert_history.append(result)
        
        # Send webhook summary
        if self.webhook_system:
            try:
                webhook_results = self.webhook_system.send_daily_summary(filtered_anomalies)
                for channel, success in webhook_results.items():
                    result = AlertResult(
                        channel=channel,
                        success=success,
                        message=f"Daily summary to {channel} {'succeeded' if success else 'failed'}"
                    )
                    results.append(result)
                    self._alert_history.append(result)
            except Exception as e:
                logger.error(f"Error sending webhook daily summary: {e}")
        
        return results
    
    def get_alert_history(self, 
                         limit: int = 100,
                         channel: Optional[str] = None) -> List[Dict]:
        """
        Get recent alert history.
        
        Args:
            limit: Maximum number of results
            channel: Optional filter by channel
            
        Returns:
            List of alert results as dictionaries
        """
        history = self._alert_history[-limit:]
        
        if channel:
            history = [a for a in history if a.channel == channel]
        
        return [a.to_dict() for a in history]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current alert system status.
        
        Returns:
            Dictionary with status information
        """
        return {
            'email_enabled': self.email_system is not None,
            'slack_enabled': bool(self.config.slack_webhook_url),
            'discord_enabled': bool(self.config.discord_webhook_url),
            'custom_webhook_enabled': bool(self.config.custom_webhook_url),
            'min_score_threshold': self.config.min_score_threshold,
            'recent_alerts_count': len(self._alert_history),
            'recent_success_rate': (
                sum(1 for a in self._alert_history[-100:] if a.success) / 
                max(len(self._alert_history[-100:]), 1)
            )
        }


# Create default alert manager instance
try:
    alert_manager = AlertManager()
except Exception as e:
    logger.warning(f"Could not initialize default alert manager: {e}")
    alert_manager = None
