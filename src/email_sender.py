"""
Email Sender Module

Handles sending email reports with attachments to multiple recipients.
Each recipient receives their own individual email with a fresh SMTP connection.
"""
import os
import json
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional


def send_email_report(
    email_config_path: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    to_addresses: Optional[List[str]] = None,
    delay_between_sends: float = 2.0
) -> bool:
    """
    Send an email with attachments to one or multiple recipients.
    
    Each recipient receives their own individual email copy with a fresh SMTP connection.

    Priority for email configuration:
    1. Environment variables (BUFFOTTE_SMTP_SERVER, etc.)
    2. Configuration file (email_config.json)

    Args:
        email_config_path: Path to the email configuration file
        subject: Email subject line
        body: Email body content (plain text)
        attachments: List of file paths to attach (optional)
        to_addresses: List of recipient email addresses (optional, overrides config)
        delay_between_sends: Delay in seconds between sending to each recipient (default: 2.0)

    Returns:
        True if at least one email sent successfully, False otherwise
    """
    # Load configuration
    cfg = _load_config(email_config_path)
    if not cfg:
        return False
    
    # Determine recipient addresses
    recipients = _get_recipients(cfg, to_addresses)
    if not recipients:
        print("❌ 没有找到收件人地址")
        return False
    
    print(f"📧 准备发送给 {len(recipients)} 位收件人:")
    for i, addr in enumerate(recipients, 1):
        print(f"   {i}. {addr}")
    print()
    
    # Track results
    successful = []
    failed = []
    
    # Send to each recipient individually with fresh connection
    for i, recipient in enumerate(recipients, 1):
        try:
            # Create email for this recipient
            msg = _create_email(
                from_addr=cfg['from_address'],
                to_addr=recipient,
                subject=subject,
                body=body,
                attachments=attachments
            )
            
            # Send email with fresh SMTP connection
            _send_single_email(cfg, msg, recipient)
            
            successful.append(recipient)
            print(f"   ✓ [{i}/{len(recipients)}] 发送成功: {recipient}")
            
            # Add delay between sends to avoid triggering spam filters
            if i < len(recipients):
                time.sleep(delay_between_sends)
                
        except Exception as e:
            failed.append(recipient)
            print(f"   ✗ [{i}/{len(recipients)}] 发送失败: {recipient} - {str(e)}")
    
    # Print summary
    print()
    print(f"📊 发送完成: 成功 {len(successful)}/{len(recipients)}")
    if failed:
        print(f"⚠️  失败的收件人: {', '.join(failed)}")
    
    return len(successful) > 0


def _load_config(config_path: str) -> Optional[dict]:
    """Load email configuration from file."""
    # Use config file
    if not os.path.exists(config_path):
        print('Email config not found; skipping email send.')
        return None
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        required = ['smtp_server', 'smtp_port', 'username', 'password', 'from_address', 'to_address']
        if not all(k in cfg for k in required):
            print('Email config missing required fields; skipping email send.')
            return None
        
        print("ℹ️  使用配置文件")
        return cfg
        
    except json.JSONDecodeError as e:
        print(f'❌ 配置文件JSON格式错误: {e}')
        return None


def _get_recipients(cfg: dict, override_addresses: Optional[List[str]]) -> List[str]:
    """Get list of recipient addresses."""
    if override_addresses:
        # Use provided addresses
        return override_addresses if isinstance(override_addresses, list) else [override_addresses]
    
    # Use config addresses
    config_to = cfg.get('to_address')
    if not config_to:
        return []
    
    # Handle both string and list formats
    if isinstance(config_to, list):
        return config_to
    elif isinstance(config_to, str):
        # Support comma-separated addresses
        return [addr.strip() for addr in config_to.split(',')]
    
    return []


def _create_email(from_addr: str, to_addr: str, subject: str, body: str, 
                  attachments: Optional[List[str]] = None) -> MIMEMultipart:
    """Create an email message with attachments."""
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    
    # Add body
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Add attachments
    if attachments:
        for file_path in attachments:
            if not os.path.exists(file_path):
                print(f"      ⚠️  附件不存在: {file_path}")
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                
                encoders.encode_base64(part)
                filename = os.path.basename(file_path)
                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                msg.attach(part)
                
            except Exception as e:
                print(f"      ⚠️  无法附加文件 {file_path}: {e}")
    
    return msg


def _send_single_email(cfg: dict, msg: MIMEMultipart, recipient: str) -> None:
    """Send a single email via SMTP with fresh connection."""
    server = None
    try:
        # Connect to SMTP server with explicit timeout
        server = smtplib.SMTP(cfg['smtp_server'], int(cfg['smtp_port']), timeout=30)
        server.set_debuglevel(0)  # Disable debug output
        
        # Enable TLS if configured
        if cfg.get('use_tls', True):
            server.starttls()
        
        # Login
        server.login(cfg['username'], cfg['password'])
        
        # Send email using sendmail instead of send_message
        # This gives us more control and avoids potential state issues
        server.sendmail(
            cfg['from_address'],
            [recipient],
            msg.as_string()
        )
        
    finally:
        # Always close connection properly
        if server:
            try:
                server.quit()
            except:
                try:
                    server.close()
                except:
                    pass
