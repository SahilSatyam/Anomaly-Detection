import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import logging
from datetime import datetime
from ..anomaly_detection.statistical_methods import AnomalyResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailAlertSystem:
    def __init__(self, 
                 smtp_server: str,
                 smtp_port: int,
                 sender_email: str,
                 sender_password: str):
        """
        Initialize the email alert system
        
        Args:
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
            sender_email (str): Sender's email address
            sender_password (str): Sender's email password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        
    def create_anomaly_email(self, 
                           recipient: str,
                           symbol: str,
                           anomalies: List[AnomalyResult]) -> MIMEMultipart:
        """
        Create email content for anomaly alerts
        
        Args:
            recipient (str): Recipient email address
            symbol (str): Stock symbol
            anomalies (List[AnomalyResult]): List of detected anomalies
            
        Returns:
            MIMEMultipart: Email message
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg['Subject'] = f"Stock Anomaly Alert - {symbol}"
        
        # Create email body
        body = f"""
        <html>
        <body>
            <h2>Stock Anomaly Alert for {symbol}</h2>
            <p>The following anomalies were detected:</p>
            <table border="1" cellpadding="5">
                <tr>
                    <th>Date</th>
                    <th>Method</th>
                    <th>Score</th>
                    <th>Details</th>
                </tr>
        """
        
        for anomaly in anomalies:
            body += f"""
                <tr>
                    <td>{anomaly.date}</td>
                    <td>{anomaly.method}</td>
                    <td>{anomaly.score:.2f}</td>
                    <td>
                        Price: ${anomaly.details.get('price', 'N/A'):.2f}<br>
                        Volume: {anomaly.details.get('volume', 'N/A'):,}<br>
                        Threshold: {anomaly.threshold:.2f}
                    </td>
                </tr>
            """
            
        body += """
            </table>
            <p>Please review these anomalies and take appropriate action.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        return msg
        
    def send_alert(self, 
                  recipient: str,
                  symbol: str,
                  anomalies: List[AnomalyResult]) -> bool:
        """
        Send email alert for detected anomalies
        
        Args:
            recipient (str): Recipient email address
            symbol (str): Stock symbol
            anomalies (List[AnomalyResult]): List of detected anomalies
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            msg = self.create_anomaly_email(recipient, symbol, anomalies)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Successfully sent anomaly alert email to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
            
    def send_daily_summary(self,
                          recipient: str,
                          daily_anomalies: Dict[str, List[AnomalyResult]]) -> bool:
        """
        Send daily summary of all detected anomalies
        
        Args:
            recipient (str): Recipient email address
            daily_anomalies (Dict[str, List[AnomalyResult]]): Dictionary of anomalies by symbol
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = f"Daily Stock Anomaly Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            body = f"""
            <html>
            <body>
                <h2>Daily Stock Anomaly Summary</h2>
                <p>Date: {datetime.now().strftime('%Y-%m-%d')}</p>
            """
            
            for symbol, anomalies in daily_anomalies.items():
                body += f"""
                    <h3>{symbol}</h3>
                    <table border="1" cellpadding="5">
                        <tr>
                            <th>Date</th>
                            <th>Method</th>
                            <th>Score</th>
                            <th>Details</th>
                        </tr>
                """
                
                for anomaly in anomalies:
                    body += f"""
                        <tr>
                            <td>{anomaly.date}</td>
                            <td>{anomaly.method}</td>
                            <td>{anomaly.score:.2f}</td>
                            <td>
                                Price: ${anomaly.details.get('price', 'N/A'):.2f}<br>
                                Volume: {anomaly.details.get('volume', 'N/A'):,}<br>
                                Threshold: {anomaly.threshold:.2f}
                            </td>
                        </tr>
                    """
                    
                body += "</table>"
                
            body += """
                <p>Please review these anomalies and take appropriate action.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Successfully sent daily summary email to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily summary email: {str(e)}")
            return False 