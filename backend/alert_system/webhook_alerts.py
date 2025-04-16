import requests
import json
import logging
from typing import List, Dict
from datetime import datetime
from ..anomaly_detection.statistical_methods import AnomalyResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookAlertSystem:
    def __init__(self, webhook_urls: Dict[str, str]):
        """
        Initialize the webhook alert system
        
        Args:
            webhook_urls (Dict[str, str]): Dictionary of webhook URLs for different platforms
                                         e.g., {'slack': 'https://hooks.slack.com/...',
                                               'discord': 'https://discord.com/api/...'}
        """
        self.webhook_urls = webhook_urls
        
    def format_slack_message(self, symbol: str, anomalies: List[AnomalyResult]) -> Dict:
        """
        Format message for Slack webhook
        
        Args:
            symbol (str): Stock symbol
            anomalies (List[AnomalyResult]): List of detected anomalies
            
        Returns:
            Dict: Formatted Slack message
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 Stock Anomaly Alert - {symbol}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "The following anomalies were detected:"
                }
            }
        ]
        
        for anomaly in anomalies:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Date:*\n{anomaly.date}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Method:*\n{anomaly.method}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Score:*\n{anomaly.score:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Price:*\n${anomaly.details.get('price', 'N/A'):.2f}"
                    }
                ]
            })
            
        return {"blocks": blocks}
        
    def format_discord_message(self, symbol: str, anomalies: List[AnomalyResult]) -> Dict:
        """
        Format message for Discord webhook
        
        Args:
            symbol (str): Stock symbol
            anomalies (List[AnomalyResult]): List of detected anomalies
            
        Returns:
            Dict: Formatted Discord message
        """
        embeds = []
        
        for anomaly in anomalies:
            embed = {
                "title": f"Stock Anomaly Alert - {symbol}",
                "color": 16711680,  # Red color
                "fields": [
                    {
                        "name": "Date",
                        "value": str(anomaly.date),
                        "inline": True
                    },
                    {
                        "name": "Method",
                        "value": anomaly.method,
                        "inline": True
                    },
                    {
                        "name": "Score",
                        "value": f"{anomaly.score:.2f}",
                        "inline": True
                    },
                    {
                        "name": "Price",
                        "value": f"${anomaly.details.get('price', 'N/A'):.2f}",
                        "inline": True
                    },
                    {
                        "name": "Volume",
                        "value": f"{anomaly.details.get('volume', 'N/A'):,}",
                        "inline": True
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
            embeds.append(embed)
            
        return {"embeds": embeds}
        
    def send_alert(self, symbol: str, anomalies: List[AnomalyResult]) -> Dict[str, bool]:
        """
        Send alerts to all configured webhooks
        
        Args:
            symbol (str): Stock symbol
            anomalies (List[AnomalyResult]): List of detected anomalies
            
        Returns:
            Dict[str, bool]: Dictionary indicating success/failure for each platform
        """
        results = {}
        
        for platform, url in self.webhook_urls.items():
            try:
                if platform == 'slack':
                    payload = self.format_slack_message(symbol, anomalies)
                elif platform == 'discord':
                    payload = self.format_discord_message(symbol, anomalies)
                else:
                    logger.warning(f"Unsupported platform: {platform}")
                    continue
                    
                response = requests.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent {platform} alert for {symbol}")
                    results[platform] = True
                else:
                    logger.error(f"Error sending {platform} alert: {response.status_code}")
                    results[platform] = False
                    
            except Exception as e:
                logger.error(f"Error sending {platform} alert: {str(e)}")
                results[platform] = False
                
        return results
        
    def send_daily_summary(self, daily_anomalies: Dict[str, List[AnomalyResult]]) -> Dict[str, bool]:
        """
        Send daily summary to all configured webhooks
        
        Args:
            daily_anomalies (Dict[str, List[AnomalyResult]]): Dictionary of anomalies by symbol
            
        Returns:
            Dict[str, bool]: Dictionary indicating success/failure for each platform
        """
        results = {}
        
        for platform, url in self.webhook_urls.items():
            try:
                if platform == 'slack':
                    blocks = [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"📊 Daily Stock Anomaly Summary - {datetime.now().strftime('%Y-%m-%d')}"
                            }
                        }
                    ]
                    
                    for symbol, anomalies in daily_anomalies.items():
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{symbol}* - {len(anomalies)} anomalies detected"
                            }
                        })
                        
                    payload = {"blocks": blocks}
                    
                elif platform == 'discord':
                    embeds = [{
                        "title": f"Daily Stock Anomaly Summary - {datetime.now().strftime('%Y-%m-%d')}",
                        "color": 3447003,  # Blue color
                        "fields": [
                            {
                                "name": symbol,
                                "value": f"{len(anomalies)} anomalies detected",
                                "inline": True
                            }
                            for symbol, anomalies in daily_anomalies.items()
                        ],
                        "timestamp": datetime.now().isoformat()
                    }]
                    payload = {"embeds": embeds}
                    
                else:
                    logger.warning(f"Unsupported platform: {platform}")
                    continue
                    
                response = requests.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent {platform} daily summary")
                    results[platform] = True
                else:
                    logger.error(f"Error sending {platform} daily summary: {response.status_code}")
                    results[platform] = False
                    
            except Exception as e:
                logger.error(f"Error sending {platform} daily summary: {str(e)}")
                results[platform] = False
                
        return results 